# Observed REZ v1 format

These notes describe independent inspection of the owner's local files and the
subset implemented by `src/reztool.cpp`. They are not a full format specification.
No third-party archive reader implementation was copied.

All numeric fields used below are unsigned 32-bit little-endian values. Archive
offsets are absolute file offsets. Read fields individually: an unpacked C++
struct would introduce host alignment and endianness assumptions.

## Header

| Offset | Interpretation used by reader |
| --- | --- |
| 0 | CR LF and a textual producer/copyright banner |
| 126 | `0x1a` terminator |
| 127 | Format version (`1`) |
| 131 | Root directory offset |
| 135 | Root directory byte count |

The archives inspected place resource data at or after offset 171. Additional
header fields exist; the current reader does not interpret them. `gamep6.REZ`
has a WinRez banner, so identifying archives by a single producer string would
reject a valid installed archive.

## Directory records

A directory is a byte span containing consecutive variable-length records:

| Field | Directory record | Resource record |
| --- | --- | --- |
| Kind | `1` | `0` |
| Offset | Child directory offset | Resource byte offset |
| Size | Child directory byte count | Resource byte count |
| Timestamp | Present, not interpreted | Present, not interpreted |
| Resource ID | — | Present, not interpreted |
| Type | — | Packed extension: bytes `LLD\0` correspond to `DLL` |
| Key count | — | Only `0` supported initially |
| Name | NUL-terminated | NUL-terminated basename |
| Description | — | NUL-terminated, observed empty |

Reject nonzero key counts until their layout is established. Resource payloads
are copied verbatim by this tool; decoded content/compression, if any, belongs to
the resource's own format. A `.LTO` or `.FXD` extension does not imply that the
payload is non-executable: inspect the bytes and PE headers.

## Reader boundaries

The tool validates file ranges before reads, limits metadata memory and depth,
rejects directory cycles and duplicate paths, and supports printable ASCII path
components without slash, backslash, or colon. High-byte filename encodings and
resource keys are explicitly unsupported. Directory offsets must be unique for
nonempty directories. Such limits are conservative inspection constraints, not
claims about every REZ producer.

Listing reads metadata only, which keeps multi-gigabyte archives practical.
Extraction requires an exact case-sensitive archive member and an explicit new
output file; it does not recursively materialize archive-controlled paths.
The caller must create the destination parent directory. It refuses existing
files, and a failed write can leave a partial output that should be removed
before retrying. Work in a trusted local output directory.

Later resource loading must separately establish Windows-style case folding and
archive precedence. The inspection tool intentionally does not guess either.
