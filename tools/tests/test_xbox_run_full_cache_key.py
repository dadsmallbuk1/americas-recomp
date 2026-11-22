import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TOOLS = Path(__file__).resolve().parent.parent


def load_run_full():
    with mock.patch.dict(os.environ, {"XBOX_RDNA2": "recomp"}):
        spec = importlib.util.spec_from_file_location("run_full_under_test", TOOLS / "xbox" / "run_full.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


class RunFullCacheKeyTest(unittest.TestCase):
    def setUp(self):
        self.run_full = load_run_full()
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        root = Path(self.directory.name)
        (root / "7.bin").write_bytes(b"\x00\x00\x81\xbf")
        (root / "7.bind").write_bytes(b"bindings")
        (root / "driver").write_bytes(b"driver")
        (root / "spirv-val").write_bytes(b"validator")
        folder = str(root) + os.sep
        patcher = mock.patch.multiple(
            self.run_full, BINS=folder, BINDS=folder, VIN=folder,
            DRIVER_CS=str(root / "driver"), DRIVER_GFX=str(root / "driver"), VAL=str(root / "spirv-val"),
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def key(self, **fields):
        return self.run_full.cache_key(dict({"idx": "7", "stage": "CS"}, **fields), False)

    def test_wave_sizes_from_the_manifest_get_different_keys(self):
        self.assertNotEqual(self.key(wave="32"), self.key(wave="64"))

    def test_a_manifest_without_a_wave_column_keeps_the_same_key(self):
        self.assertEqual(self.key(), self.key(wave=""))


if __name__ == "__main__":
    unittest.main()
