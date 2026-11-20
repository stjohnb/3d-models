"""Unit tests for external_assets.py. Pure stdlib."""

import contextlib
import io
import json
import os
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from external_assets import (
    external_assets,
    external_assets_for,
    main,
    project_manifest,
    unstageable_inputs_for,
)


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


class ContainmentTests(unittest.TestCase):
    def test_traversal_asset_is_not_bundled(self):
        with tempfile.TemporaryDirectory() as outside:
            outside_file = os.path.join(outside, "outside.stl")
            with open(outside_file, "w") as f:
                f.write("secret")
            with tempfile.TemporaryDirectory() as tmp:
                proj = os.path.join(tmp, "proj")
                os.makedirs(proj)
                target = os.path.relpath(outside_file, proj)
                with open(os.path.join(proj, "a.scad"), "w") as f:
                    f.write('import("%s");\n' % target)
                original = os.getcwd()
                os.chdir(tmp)
                try:
                    self.assertEqual(external_assets_for("proj/a.scad", "proj"), [])
                    self.assertEqual(external_assets("proj"), [])
                finally:
                    os.chdir(original)

    def test_git_config_is_not_bundled(self):
        with tree({
            "proj/a.scad": 'import("../.git/config");\n',
            ".git/config": "[remote]\n  url = https://x:TOKEN@github.com/o/r\n",
        }):
            self.assertEqual(external_assets_for("proj/a.scad", "proj"), [])
            self.assertEqual(external_assets("proj"), [])

    def test_scans_reference_still_bundled(self):
        with tree({
            "proj/a.scad": 'import("../scans/tube/tube-reference.stl");\n',
            "scans/tube/tube-reference.stl": "stl",
        }):
            self.assertEqual(
                external_assets_for("proj/a.scad", "proj"),
                ["scans/tube/tube-reference.stl"],
            )
            self.assertEqual(
                external_assets("proj"), ["scans/tube/tube-reference.stl"]
            )


# A project including another project's shared library by relative path
# (long-drawer-organiser -> drawer-organiser, issue clw_01M4R6ED006HYSY6F15NMYHMGD).
CROSS_PROJECT = {
    "proj/part.scad": "include <_own.scad>\ncube(size);\n",
    "proj/_own.scad": "include <../other/_lib.scad>\nsize = 1;\n",
    "other/_lib.scad": "include <_base.scad>\nmodule lib() { base(); }\n",
    "other/_base.scad": "module base() { cube(1); }\n",
    "other/thing.scad": 'lib();\nsurface(file = "map.png");\n',
    "other/map.png": "png",
    "other/unused.png": "png",
}


class CrossProjectTests(unittest.TestCase):
    def test_zip_extras_include_the_library_chain(self):
        with tree(CROSS_PROJECT):
            self.assertEqual(
                external_assets_for("proj/part.scad", "proj"),
                ["other/_base.scad", "other/_lib.scad"],
            )
            self.assertEqual(
                external_assets("proj"), ["other/_base.scad", "other/_lib.scad"]
            )

    def test_cross_project_library_is_stageable(self):
        with tree(CROSS_PROJECT):
            self.assertEqual(unstageable_inputs_for("proj/part.scad", "proj"), [])

    def test_scan_import_through_library_is_unstageable(self):
        files = dict(CROSS_PROJECT)
        files["other/_base.scad"] = 'module base() { import("../scans/x/x.stl"); }\n'
        files["scans/x/x.stl"] = "stl"
        with tree(files):
            self.assertEqual(
                unstageable_inputs_for("proj/part.scad", "proj"), ["scans/x/x.stl"]
            )

    def test_missing_include_is_unstageable(self):
        with tree({"proj/a.scad": "include <../other/_gone.scad>\n"}):
            self.assertEqual(
                unstageable_inputs_for("proj/a.scad", "proj"),
                ["../other/_gone.scad"],
            )

    def test_manifest_lists_the_chain_project_relative(self):
        with tree(CROSS_PROJECT):
            self.assertEqual(
                project_manifest("proj"),
                ["../other/_base.scad", "../other/_lib.scad", "_own.scad", "part.scad"],
            )

    def test_manifest_keeps_variable_named_heightmaps(self):
        """surface(file = var) is invisible to collect_inputs; the basename rule stays."""
        with tree({
            "proj/a.scad": 'f = "heightmap.png";\nsurface(file = f);\n',
            "proj/heightmap.png": "png",
            "proj/screenshot.png": "png",
        }):
            self.assertEqual(project_manifest("proj"), ["a.scad", "heightmap.png"])

    def test_stage_writes_chain_and_manifests(self):
        with tree(CROSS_PROJECT) as root:
            self.assertEqual(main(["--stage", "site/sources"]), 0)
            sources = root / "site" / "sources"
            self.assertEqual(
                json.loads((sources / "proj" / "manifest.json").read_text()),
                ["../other/_base.scad", "../other/_lib.scad", "_own.scad", "part.scad"],
            )
            self.assertEqual(
                json.loads((sources / "other" / "manifest.json").read_text()),
                ["_base.scad", "_lib.scad", "map.png", "thing.scad"],
            )
            staged = sorted(
                str(p.relative_to(sources)) for p in sources.rglob("*") if p.is_file()
            )
            self.assertEqual(staged, [
                "other/_base.scad", "other/_lib.scad", "other/manifest.json",
                "other/map.png", "other/thing.scad",
                "proj/_own.scad", "proj/manifest.json", "proj/part.scad",
            ])

    def test_manifest_cli_prints_json(self):
        with tree(CROSS_PROJECT):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(main(["--manifest", "proj"]), 0)
            self.assertIn("../other/_lib.scad", json.loads(out.getvalue()))


if __name__ == "__main__":
    unittest.main()
