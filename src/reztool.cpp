// REZ v1 reader derived from local archive observations; see docs/REZ_FORMAT.md.
#include <algorithm>
#include <array>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

namespace fs = std::filesystem;
using Bytes = std::vector<unsigned char>;

struct Cursor {
    const Bytes& data;
    std::size_t pos = 0;
    std::uint32_t u32() {
        if (data.size() - pos < 4) throw std::runtime_error("truncated integer");
        std::uint32_t value = 0;
        for (unsigned i = 0; i < 4; ++i)
            value |= static_cast<std::uint32_t>(data[pos++]) << (i * 8);
        return value;
    }
    std::string string() {
        std::string value;
        while (pos < data.size()) {
            const auto c = data[pos++];
            if (c == 0) return value;
            value.push_back(static_cast<char>(c));
        }
        throw std::runtime_error("unterminated string");
    }
};

void validate_component(const std::string& name) {
    if (name.empty() || name == "." || name == "..")
        throw std::runtime_error("invalid empty or relative name");
    for (const unsigned char c : name)
        if (c < 32 || c > 126 || c == '/' || c == '\\' || c == ':')
            throw std::runtime_error("unsupported character in member name");
}

struct Entry {
    std::string path;
    std::uint32_t offset;
    std::uint32_t size;
};

class Archive {
public:
    explicit Archive(const fs::path& path) : input_(path, std::ios::binary) {
        if (!input_) throw std::runtime_error("cannot open archive");
        size_ = fs::file_size(path);
        auto header = read(0, 139);
        if (header[0] != 13 || header[1] != 10 || header[126] != 26)
            throw std::runtime_error("not a recognized REZ header");
        Cursor cursor{header, 127};
        if (cursor.u32() != 1) throw std::runtime_error("only REZ version 1 is supported");
        const auto offset = cursor.u32();
        const auto length = cursor.u32();
        directory(offset, length, "", 0);
        std::sort(entries.begin(), entries.end(), [](const Entry& a, const Entry& b) {
            return a.path < b.path;
        });
    }

    std::vector<Entry> entries;

    void extract(const Entry& entry, const fs::path& output) {
        if (fs::exists(output) || fs::is_symlink(output))
            throw std::runtime_error("output already exists; choose a new path");
        std::ofstream dest(output, std::ios::binary);
        if (!dest) throw std::runtime_error("cannot create output (parent must exist)");
        input_.clear();
        input_.seekg(entry.offset);
        std::array<char, 65536> buffer{};
        std::uint64_t remaining = entry.size;
        while (remaining != 0) {
            const auto count = static_cast<std::streamsize>(std::min<std::uint64_t>(remaining, buffer.size()));
            if (!input_.read(buffer.data(), count) || !dest.write(buffer.data(), count))
                throw std::runtime_error("extraction I/O failure; output may be partial");
            remaining -= static_cast<std::uint64_t>(count);
        }
        dest.close();
        if (!dest) throw std::runtime_error("cannot finish writing output");
    }

private:
    std::ifstream input_;
    std::uint64_t size_ = 0;
    std::uint64_t metadata_bytes_ = 0;
    std::set<std::uint32_t> visited_;
    std::set<std::string> names_;
    std::size_t records_ = 0;

    void bounds(std::uint64_t offset, std::uint64_t length) const {
        if (offset > size_ || length > size_ - offset)
            throw std::runtime_error("archive range exceeds file size");
    }
    Bytes read(std::uint32_t offset, std::uint32_t length) {
        bounds(offset, length);
        if (length > 64 * 1024 * 1024)
            throw std::runtime_error("directory exceeds 64 MiB inspection limit");
        Bytes data(length);
        input_.clear();
        input_.seekg(offset);
        if (length && !input_.read(reinterpret_cast<char*>(data.data()), length))
            throw std::runtime_error("cannot read archive");
        return data;
    }
    void directory(std::uint32_t offset, std::uint32_t length,
                   const std::string& prefix, unsigned depth) {
        bounds(offset, length);
        if (depth > 128) throw std::runtime_error("directory nesting limit exceeded");
        if (length == 0) return;
        if (!visited_.insert(offset).second)
            throw std::runtime_error("repeated or cyclic directory offset");
        metadata_bytes_ += length;
        if (metadata_bytes_ > 128 * 1024 * 1024)
            throw std::runtime_error("metadata exceeds 128 MiB inspection limit");
        const auto data = read(offset, length);
        Cursor cursor{data};
        while (cursor.pos < data.size()) {
            if (++records_ > 1000000) throw std::runtime_error("record limit exceeded");
            const auto kind = cursor.u32();
            const auto member_offset = cursor.u32();
            const auto member_size = cursor.u32();
            cursor.u32(); // Timestamp: retain format boundary, not interpreted here.
            if (kind == 1) {
                const auto name = cursor.string();
                validate_component(name);
                const auto full = prefix + name;
                if (!names_.insert(full).second) throw std::runtime_error("duplicate member path");
                directory(member_offset, member_size, full + "/", depth + 1);
            } else if (kind == 0) {
                cursor.u32(); // Resource ID.
                const auto type = cursor.u32();
                const auto keys = cursor.u32();
                if (keys != 0) throw std::runtime_error("resource keys are not supported yet");
                const auto name = cursor.string();
                cursor.string(); // Resource description (empty in observed files).
                validate_component(name);
                std::string extension;
                for (int shift = 24; shift >= 0; shift -= 8) {
                    const auto c = static_cast<char>((type >> shift) & 255);
                    if (c != 0) extension.push_back(c);
                }
                if (!extension.empty()) validate_component(extension);
                const auto full = prefix + name + (extension.empty() ? "" : "." + extension);
                if (!names_.insert(full).second) throw std::runtime_error("duplicate member path");
                bounds(member_offset, member_size);
                entries.push_back({full, member_offset, member_size});
            } else {
                throw std::runtime_error("unknown directory record kind");
            }
        }
    }
};

int main(int argc, char** argv) {
    try {
        if (argc < 3 || (std::string(argv[1]) != "list" && std::string(argv[1]) != "extract")) {
            std::cerr << "Usage: reztool list ARCHIVE\n"
                         "       reztool extract ARCHIVE MEMBER OUTPUT\n";
            return 2;
        }
        const bool extract = std::string(argv[1]) == "extract";
        if (argc != (extract ? 5 : 3)) throw std::runtime_error("incorrect argument count");
        Archive archive(argv[2]);
        if (!extract) {
            std::cout << "path\toffset\tsize\n";
            for (const auto& entry : archive.entries)
                std::cout << entry.path << '\t' << entry.offset << '\t' << entry.size << '\n';
        } else {
            const auto it = std::find_if(archive.entries.begin(), archive.entries.end(), [&](const Entry& e) {
                return e.path == argv[3];
            });
            if (it == archive.entries.end()) throw std::runtime_error("member not found (names are case sensitive)");
            archive.extract(*it, argv[4]);
        }
    } catch (const std::exception& error) {
        std::cerr << "reztool: " << error.what() << '\n';
        return 1;
    }
}
