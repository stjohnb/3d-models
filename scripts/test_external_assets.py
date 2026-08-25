"""Unit tests for external_assets.py. Pure stdlib."""

import contextlib
import io
import os
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from external_assets import external_assets, external_assets_for, main


@contextlib.contextmanager
def tree(files):
    """A temp directory populated with {relative path: contents}, cwd'd into."""
    original = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        for rel, contents in files.items():
            path = pathlib.Path(tmp) / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents)
        os.chdir(tmp)
        try:
            yield pathlib.Path(tmp)
        finally:
            os.chdir(original)


class ExternalAssetTests(unittest.TestCase):
    def test_reports_only_assets_outside_the_project(self):
        with tree({
            "proj/a.scad": 'import("../scans/tube/tube-reference.stl");\n'
                           'surface("local.png");\n',
            "proj/local.png": "png",
            "scans/tube/tube-reference.stl": "stl",
        }):
            self.assertEqual(
                external_assets("proj"), ["scans/tube/tube-reference.stl"]
            )

    def test_self_contained_project_reports_nothing(self):
        with tree({
            "proj/a.scad": 'include <_lib.scad>\nsurface("heightmap.png");\n',
            "proj/_lib.scad": "module thing() { cube(1); }\n",
            "proj/heightmap.png": "png",
        }):
            self.assertEqual(external_assets("proj"), [])

    def test_missing_asset_is_not_reported(self):
        """collect_inputs leaves unresolvable targets out of asset_files."""
        with tree({"proj/a.scad": 'import("../scans/gone/gone.stl");\n'}):
            self.assertEqual(external_assets("proj"), [])

    def test_main_prints_one_asset_per_line(self):
        with tree({
            "proj/a.scad": 'import("../scans/tube/tube-reference.stl");\n',
            "scans/tube/tube-reference.stl": "stl",
        }):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(main(["proj"]), 0)
            self.assertEqual(out.getvalue(), "scans/tube/tube-reference.stl\n")


class PerRenderableTests(unittest.TestCase):
    def test_only_the_importing_renderable_is_rejected(self):
        with tree({
            "proj/importer.scad": 'import("../scans/tube/tube-reference.stl");\n',
            "proj/clean.scad": "cube(10);\n",
            "scans/tube/tube-reference.stl": "stl",
        }):
            self.assertEqual(external_assets_for("proj/clean.scad", "proj"), [])
            self.assertEqual(
                external_assets_for("proj/importer.scad", "proj"),
                ["scans/tube/tube-reference.stl"],
            )
            self.assertEqual(
                external_assets("proj"), ["scans/tube/tube-reference.stl"]
            )

    def test_transitive_include_is_followed(self):
        with tree({
            "proj/a.scad": "include <_lib.scad>\n",
            "proj/_lib.scad": 'import("../scans/tube/tube-reference.stl");\n',
            "scans/tube/tube-reference.stl": "stl",
        }):
            self.assertEqual(
                external_assets_for("proj/a.scad", "proj"),
                ["scans/tube/tube-reference.stl"],
            )

    def test_local_assets_are_not_reported(self):
        with tree({
            "proj/a.scad": 'surface("heightmap.png");\n',
            "proj/heightmap.png": "png",
        }):
            self.assertEqual(external_assets_for("proj/a.scad", "proj"), [])

    def test_missing_external_asset_is_not_reported(self):
        with tree({"proj/a.scad": 'import("../scans/gone/gone.stl");\n'}):
            self.assertEqual(external_assets_for("proj/a.scad", "proj"), [])


if __name__ == "__main__":
    unittest.main()
