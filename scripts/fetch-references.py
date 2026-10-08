#!/usr/bin/env python3
"""Fetch only the pinned, hashed reference files listed in the authored manifest."""
import hashlib
import json
from pathlib import Path
import urllib.request

root = Path(__file__).resolve().parent.parent
manifest = json.loads((root / "docs/references/lithtech.json").read_text())
output = root / "local/references" / ("lithtech-" + manifest["revision"])
for item in manifest["files"]:
    relative = Path(item["path"])
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Invalid reference path")
    destination = output / relative
    if destination.exists() and hashlib.sha256(destination.read_bytes()).hexdigest() == item["sha256"]:
        continue
    data = urllib.request.urlopen(item["url"], timeout=30).read()
    if hashlib.sha256(data).hexdigest() != item["sha256"]:
        raise ValueError(f"Reference hash mismatch: {relative}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
output.mkdir(parents=True, exist_ok=True)
(output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(f"Verified {len(manifest['files'])} reference files at {manifest['revision']}")
