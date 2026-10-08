#!/usr/bin/env python3
"""Compare PE section bytes and report bounded, addressable change spans."""
import argparse
import hashlib
import json
from pathlib import Path
import pefile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("modified", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    before, after = args.baseline.read_bytes(), args.modified.read_bytes()
    report = {"baseline": str(args.baseline), "modified": str(args.modified),
              "baseline_sha256": hashlib.sha256(before).hexdigest(),
              "modified_sha256": hashlib.sha256(after).hexdigest(), "sections": []}
    with pefile.PE(data=before) as left, pefile.PE(data=after) as right:
        previous = {s.Name: s for s in left.sections}
        for section in right.sections:
            name = section.Name.rstrip(b"\0").decode("ascii", errors="replace")
            item = {"name": name}
            report["sections"].append(item)
            old = previous.get(section.Name)
            if old is None:
                item["status"] = "new section"
                continue
            a, b = old.get_data(), section.get_data()
            item.update({"baseline_size": len(a), "modified_size": len(b),
                         "same_rva": old.VirtualAddress == section.VirtualAddress,
                         "identical": a == b,
                         "different_bytes_in_common_length": sum(x != y for x, y in zip(a, b)),
                         "size_delta": len(b) - len(a), "spans": []})
            start = None
            count = 0
            for offset in range(min(len(a), len(b)) + 1):
                differs = offset < min(len(a), len(b)) and a[offset] != b[offset]
                if differs and start is None:
                    start = offset
                if not differs and start is not None:
                    count += 1
                    if len(item["spans"]) < 128:
                        item["spans"].append({"baseline_rva": hex(old.VirtualAddress + start),
                                               "modified_rva": hex(section.VirtualAddress + start),
                                               "length": offset - start,
                                               "before_first_16": a[start:min(offset, start+16)].hex(),
                                               "after_first_16": b[start:min(offset, start+16)].hex()})
                    start = None
            item["span_count"] = count
        report["removed_sections"] = [s.Name.rstrip(b"\0").decode("ascii", errors="replace")
                                      for s in left.sections if s.Name not in {t.Name for t in right.sections}]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
