"""Synthetic REZ fixtures: no game data is required for these tests."""
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(sys.argv.pop(1)).resolve()


def resource(name=b"TEST", offset=171, size=4, keys=0):
    return struct.pack("<7I", 0, offset, size, 0, 0, int.from_bytes(b"LLD\0", "little"), keys) + name + b"\0\0"


def directory(name, offset, size):
    return struct.pack("<4I", 1, offset, size, 0) + name + b"\0"


def archive(records, payload=b"MZ!!", version=1):
    header = bytearray(171)
    header[:2] = b"\r\n"
    header[126] = 26
    struct.pack_into("<3I", header, 127, version, 171 + len(payload), len(records))
    return bytes(header) + payload + records


class RezTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.input = self.root / "sample.rez"

    def run_tool(self, data, *args):
        self.input.write_bytes(data)
        return subprocess.run([str(TOOL), args[0], str(self.input), *args[1:]],
                              capture_output=True, text=True)

    def test_list_and_extract(self):
        data = archive(resource())
        result = self.run_tool(data, "list")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "path\toffset\tsize\nTEST.DLL\t171\t4\n")
        output = self.root / "test.dll"
        result = self.run_tool(data, "extract", "TEST.DLL", str(output))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output.read_bytes(), b"MZ!!")

    def test_nested(self):
        child = resource()
        data = archive(directory(b"SUB", 175, len(child)), b"MZ!!" + child)
        result = self.run_tool(data, "list")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("SUB/TEST.DLL\t171\t4", result.stdout)

    def test_refuse_overwrite(self):
        output = self.root / "exists.dll"
        output.write_bytes(b"keep")
        result = self.run_tool(archive(resource()), "extract", "TEST.DLL", str(output))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output.read_bytes(), b"keep")

    def test_missing_member_does_not_create_output(self):
        output = self.root / "missing.dll"
        result = self.run_tool(archive(resource()), "extract", "MISSING", str(output))
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(output.exists())

    def test_bad_inputs(self):
        cyclic = directory(b"LOOP", 175, 21)
        cases = {
            "short header": b"bad",
            "unsupported version": archive(b"", version=2),
            "payload out of bounds": archive(resource(offset=0xFFFFFFFF)),
            "payload length overflow": archive(resource(size=0xFFFFFFFF)),
            "truncated record": archive(b"\0\0"),
            "unterminated name": archive(resource()[:-2]),
            "keys": archive(resource(keys=1)),
            "traversal name": archive(resource(name=b"../BAD")),
            "control name": archive(resource(name=b"BAD\tNAME")),
            "duplicate member": archive(resource() + resource()),
            "cyclic directory": archive(cyclic),
            "unknown kind": archive(struct.pack("<4I", 9, 0, 0, 0)),
        }
        for name, data in cases.items():
            with self.subTest(name=name):
                result = self.run_tool(data, "list")
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue(result.stderr.startswith("reztool:"), result.stderr)


if __name__ == "__main__":
    unittest.main()
