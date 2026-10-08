"""Exercise extension-independent discovery and extraction integrity."""
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

TOOL = Path(sys.argv.pop(1)).resolve()
CATALOG = Path(__file__).resolve().parents[1] / "scripts/catalog.py"


def fixture():
    header = bytearray(171)
    header[:2] = b"\r\n"
    header[126] = 26
    payload = b"MZcandidateDATA"
    def entry(name, offset, size, extension):
        kind = int.from_bytes(extension[::-1].ljust(4, b"\0"), "little")
        return struct.pack("<7I", 0, offset, size, 0, 0, kind, 0) + name + b"\0\0"
    records = entry(b"HIDDEN", 171, 11, b"BIN") + entry(b"NOT_CODE", 182, 4, b"DLL")
    struct.pack_into("<3I", header, 127, 1, 171 + len(payload), len(records))
    return bytes(header) + payload + records


class CatalogTests(unittest.TestCase):
    def test_nonstandard_extension_and_repeat_integrity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            game, output = root / "game", root / "output"
            game.mkdir()
            original = fixture()
            (game / "sample.rez").write_bytes(original)
            command = [sys.executable, str(CATALOG), str(game), "--tool", str(TOOL), "--out", str(output)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads((output / "archives.json").read_text())
            modules = manifest["archives"][0]["modules"]
            self.assertEqual([m["member"] for m in modules], ["HIDDEN.BIN"])
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
            (output / modules[0]["extracted"]).write_bytes(b"changed")
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("differs from source", result.stderr)
            self.assertEqual((game / "sample.rez").read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
