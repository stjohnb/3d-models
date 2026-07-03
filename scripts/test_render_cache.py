"""Unit tests for render_cache.py.

Each test builds a synthetic project in a temporary directory and chdirs into
it (the CI render step always runs from the repo root and passes repo-relative
paths, so os.path.relpath-based keys depend on cwd). No OpenSCAD needed — the
module is pure hashing.
"""

import os
import tempfile
import unittest

from render_cache import collect_inputs, compute_key

VERSION = "OpenSCAD 2021.01"


class RenderCacheTestCase(unittest.TestCase):
    def setUp(self):
        self._orig_cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        os.chdir(self._tmp.name)

    def tearDown(self):
        os.chdir(self._orig_cwd)
        self._tmp.cleanup()

    def _write(self, name, content, mode="w"):
        path = os.path.join(self._tmp.name, name)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, mode) as f:
            f.write(content)
        return name

    def test_deterministic(self):
        self._write("a.scad", "cube(10);\n")
        k1 = compute_key("a.scad", VERSION)
        k2 = compute_key("a.scad", VERSION)
        self.assertEqual(k1, k2)

    def test_renderable_content_change(self):
        self._write("a.scad", "cube(10);\n")
        before = compute_key("a.scad", VERSION)
        self._write("a.scad", "cube(20);\n")
        after = compute_key("a.scad", VERSION)
        self.assertNotEqual(before, after)

    def test_transitive_library_change(self):
        self._write("_lib.scad", "module m() { cube(1); }\n")
        self._write("a.scad", "include <_lib.scad>\nm();\n")
        before = compute_key("a.scad", VERSION)
        self._write("_lib.scad", "module m() { cube(2); }\n")
        after = compute_key("a.scad", VERSION)
        self.assertNotEqual(before, after)

    def test_openscad_version_change(self):
        self._write("a.scad", "cube(10);\n")
        k1 = compute_key("a.scad", "OpenSCAD 2021.01")
        k2 = compute_key("a.scad", "OpenSCAD 2025.01")
        self.assertNotEqual(k1, k2)

    def test_binary_asset_change(self):
        self._write("h.png", b"\x89PNG\x00\x01\x02\x03", mode="wb")
        self._write("a.scad", 'surface(file="h.png");\n')
        before = compute_key("a.scad", VERSION)
        self._write("h.png", b"\x89PNG\x00\x01\x02\xff", mode="wb")
        after = compute_key("a.scad", VERSION)
        self.assertNotEqual(before, after)

    def test_per_model_scoping(self):
        self._write("a.scad", "cube(10);\n")
        self._write("b.scad", "sphere(5);\n")
        before = compute_key("a.scad", VERSION)
        self._write("b.scad", "sphere(99);\n")
        after = compute_key("a.scad", VERSION)
        self.assertEqual(before, after)

    def test_cycle_safety(self):
        self._write("a.scad", "include <b.scad>\ncube(1);\n")
        self._write("b.scad", "include <a.scad>\nsphere(1);\n")
        scad_files, _, _ = collect_inputs("a.scad")
        rels = {os.path.relpath(p) for p in scad_files}
        self.assertIn("a.scad", rels)
        self.assertIn("b.scad", rels)
        # Should not hang or raise.
        self.assertIsInstance(compute_key("a.scad", VERSION), str)

    def test_missing_include(self):
        self._write("a.scad", "include <_nope.scad>\ncube(1);\n")
        with_include = compute_key("a.scad", VERSION)
        self._write("a.scad", "cube(1);\n")
        without_include = compute_key("a.scad", VERSION)
        self.assertNotEqual(with_include, without_include)


if __name__ == "__main__":
    unittest.main()
