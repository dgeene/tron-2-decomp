#!/usr/bin/env python3
"""Catalog installed REZs and extract PE modules with their archive provenance."""
import argparse
import csv
import hashlib
import io
import json
import subprocess
from pathlib import Path


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--tool", type=Path, default=Path("build/dev/reztool"))
    parser.add_argument("--out", type=Path, default=Path("local/catalog"))
    args = parser.parse_args()
    root = args.directory.resolve(strict=True)
    tool = args.tool.resolve(strict=True)
    output = args.out.resolve()
    if output.is_relative_to(root):
        parser.error("output must be outside the source installation")
    output.mkdir(parents=True, exist_ok=True)
    report = {"schema_version": 1, "archives": []}
    archives = sorted(p for p in root.rglob("*")
                      if p.is_file() and not p.is_symlink() and p.suffix.lower() == ".rez")
    for archive in archives:
        relative = archive.relative_to(root).as_posix()
        print(f"Cataloging {relative}", flush=True)
        digest = sha256(archive)
        run = subprocess.run([str(tool), "list", str(archive)], check=True,
                             capture_output=True, text=True)
        entries = list(csv.DictReader(io.StringIO(run.stdout), delimiter="\t"))
        target = output / f"{archive.name}_{digest[:16]}"
        target.mkdir(parents=True, exist_ok=True)
        (target / "members.tsv").write_text(run.stdout)
        record = {"path": relative, "sha256": digest, "entries": len(entries),
                  "catalog": str((target / "members.tsv").relative_to(output)), "modules": []}
        with archive.open("rb") as stream:
            for entry in entries:
                member = Path(entry["path"])
                if member.suffix.lower() not in {".dll", ".exe", ".lto", ".fxd"}:
                    continue
                if member.is_absolute() or ".." in member.parts:
                    raise ValueError(f"Unsafe archive member: {member}")
                offset, size = int(entry["offset"]), int(entry["size"])
                stream.seek(offset)
                if size < 2 or stream.read(2) != b"MZ":
                    continue
                destination = target / "modules" / member
                destination.parent.mkdir(parents=True, exist_ok=True)
                if not destination.exists():
                    subprocess.run([str(tool), "extract", str(archive), entry["path"],
                                    str(destination)], check=True)
                # Verify against the current source bytes, including on repeated runs.
                stream.seek(offset)
                expected = hashlib.sha256()
                remaining = size
                while remaining:
                    chunk = stream.read(min(remaining, 1024 * 1024))
                    if not chunk:
                        raise ValueError("Source archive changed or truncated during extraction")
                    expected.update(chunk)
                    remaining -= len(chunk)
                module_digest = sha256(destination)
                if module_digest != expected.hexdigest():
                    raise ValueError(f"Existing extract differs from source: {destination}")
                record["modules"].append({"member": entry["path"], "offset": offset, "size": size,
                                          "sha256": module_digest,
                                          "extracted": str(destination.relative_to(output))})
        report["archives"].append(record)
        print(f"  {len(entries)} resources, {len(record['modules'])} PE candidates", flush=True)
    (output / "archives.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
