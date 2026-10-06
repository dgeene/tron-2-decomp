#!/usr/bin/env python3
"""Hash local game artifacts and describe PE images without executing them."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pefile


def decoded(value):
    return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else str(value)


def describe_pe(path):
    with pefile.PE(str(path), fast_load=False) as pe:
        imports = []
        for desc in getattr(pe, "DIRECTORY_ENTRY_IMPORT", []):
            imports.append({"dll": decoded(desc.dll), "symbols": [
                decoded(i.name) if i.name else f"ordinal:{i.ordinal}" for i in desc.imports
            ]})
        exports = [{"name": decoded(e.name) if e.name else None,
                    "ordinal": e.ordinal, "rva": hex(e.address),
                    "forwarder": decoded(e.forwarder) if e.forwarder else None}
                   for e in getattr(getattr(pe, "DIRECTORY_ENTRY_EXPORT", None), "symbols", [])]
        versions = {}
        for group in getattr(pe, "FileInfo", []):
            for item in group:
                for table in getattr(item, "StringTable", []):
                    versions.update({decoded(k): decoded(v) for k, v in table.entries.items()})
        return {
            "machine": hex(pe.FILE_HEADER.Machine),
            "optional_header_magic": hex(pe.OPTIONAL_HEADER.Magic),
            "coff_timestamp_raw": pe.FILE_HEADER.TimeDateStamp,
            "coff_timestamp_utc": datetime.fromtimestamp(pe.FILE_HEADER.TimeDateStamp, timezone.utc).isoformat(),
            "linker_version": f"{pe.OPTIONAL_HEADER.MajorLinkerVersion}.{pe.OPTIONAL_HEADER.MinorLinkerVersion}",
            "image_base": hex(pe.OPTIONAL_HEADER.ImageBase),
            "entry_point_rva": hex(pe.OPTIONAL_HEADER.AddressOfEntryPoint),
            "entry_point_va": hex(pe.OPTIONAL_HEADER.ImageBase + pe.OPTIONAL_HEADER.AddressOfEntryPoint),
            "sections": [{"name": decoded(s.Name.rstrip(b"\0")),
                          "rva": hex(s.VirtualAddress), "virtual_size": s.Misc_VirtualSize,
                          "file_offset": s.PointerToRawData, "file_size": s.SizeOfRawData,
                          "characteristics": hex(s.Characteristics)} for s in pe.sections],
            "imports": imports, "exports": exports, "version_strings": versions,
            "warnings": pe.get_warnings(),
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    root = args.directory.resolve(strict=True)
    if not root.is_dir():
        parser.error("directory must be an existing installation or module directory")
    records = []
    errors = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        if path.suffix.lower() not in {".exe", ".dll", ".rez", ".lto", ".fxd"}:
            continue
        relative = path.relative_to(root).as_posix()
        print(f"Inspecting {relative}", flush=True)
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        record = {"path": relative, "size": path.stat().st_size, "sha256": digest}
        if path.suffix.lower() != ".rez":
            try:
                record["pe"] = describe_pe(path)
            except (pefile.PEFormatError, ValueError, OSError) as error:
                record["pe_error"] = str(error)
                errors.append(relative)
        records.append(record)
    by_path = {r["path"].lower(): r for r in records}
    backups = []
    for record in records:
        if record["path"].lower().startswith("kamodbackups/"):
            installed = by_path.get(Path(record["path"]).name.lower())
            if installed:
                backups.append({"installed": installed["path"], "backup": record["path"],
                                "identical": installed["sha256"] == record["sha256"]})
    report = {"schema_version": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
              "files": records, "backup_comparisons": backups, "pe_errors": errors}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Wrote {len(records)} records to {args.out}; {len(errors)} PE parse errors")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
