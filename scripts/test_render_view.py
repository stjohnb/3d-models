"""Unit tests for render_view.py.

Tests argument parsing and openscad argv assembly only — no openscad invocation.
Run with: python3 -m unittest scripts/test_render_view.py
"""

import os
import pathlib
import shutil
import stat
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from render_view import (
    build_openscad_argv,
    parse_args,
    resolve_output_path,
    PRESETS,
    PRESETS_Y_UP,
)


def _args(**kwargs):
    """Build an args namespace with defaults matching parse_args() then override."""
    import types
    defaults = dict(
        scad_file=pathlib.Path("test.scad"),
        output=pathlib.Path("/tmp/render.png"),
        view="iso",
        camera=None,
        projection=None,
        imgsize="800x600",
        viewall=True,
        autocenter=True,
        color_scheme=None,
        defines=[],
        y_up=False,
        quiet=False,
    )
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


class TestArgvPresets(unittest.TestCase):

    def _argv(self, **kwargs):
        return build_openscad_argv(_args(**kwargs))

    def test_iso_preset(self):
        argv = self._argv(view="iso")
        self.assertIn(f"--camera={PRESETS['iso']['camera']}", argv)
        self.assertIn("--projection=perspective", argv)

    def test_top_preset(self):
        argv = self._argv(view="top")
        self.assertIn(f"--camera={PRESETS['top']['camera']}", argv)
        self.assertIn("--projection=ortho", argv)

    def test_bottom_preset(self):
        argv = self._argv(view="bottom")
        self.assertIn(f"--camera={PRESETS['bottom']['camera']}", argv)
        self.assertIn("--projection=ortho", argv)

    def test_front_preset(self):
        argv = self._argv(view="front")
        self.assertIn(f"--camera={PRESETS['front']['camera']}", argv)
        self.assertIn("--projection=ortho", argv)

    def test_custom_with_camera(self):
        camera = "10,20,30,45,0,90,300"
        argv = self._argv(view="custom", camera=camera)
        self.assertIn(f"--camera={camera}", argv)

    def test_y_up_top_preset(self):
        argv = self._argv(view="top", y_up=True)
        self.assertIn(f"--camera={PRESETS_Y_UP['top']['camera']}", argv)
        self.assertNotIn(f"--camera={PRESETS['top']['camera']}", argv)

    def test_y_up_bottom_preset(self):
        argv = self._argv(view="bottom", y_up=True)
        self.assertIn(f"--camera={PRESETS_Y_UP['bottom']['camera']}", argv)

    def test_y_up_differs_from_z_up(self):
        self.assertNotEqual(PRESETS["top"]["camera"], PRESETS_Y_UP["top"]["camera"])
        self.assertNotEqual(PRESETS["bottom"]["camera"], PRESETS_Y_UP["bottom"]["camera"])


class TestArgvOptions(unittest.TestCase):

    def _argv(self, **kwargs):
        return build_openscad_argv(_args(**kwargs))

    def test_imgsize_roundtrip(self):
        argv = self._argv(imgsize="1024x768")
        self.assertIn("--imgsize=1024,768", argv)

    def test_default_imgsize(self):
        argv = self._argv()
        self.assertIn("--imgsize=800,600", argv)

    def test_no_viewall(self):
        argv = self._argv(viewall=False)
        self.assertNotIn("--viewall", argv)

    def test_viewall_default(self):
        argv = self._argv()
        self.assertIn("--viewall", argv)

    def test_no_autocenter(self):
        argv = self._argv(autocenter=False)
        self.assertNotIn("--autocenter", argv)

    def test_autocenter_default(self):
        argv = self._argv()
        self.assertIn("--autocenter", argv)

    def test_defines(self):
        argv = self._argv(defines=["foo=1", "bar=2"])
        # Each define should appear as a separate -D <value> pair
        self.assertIn("-D", argv)
        idx_foo = argv.index("-D")
        self.assertEqual(argv[idx_foo + 1], "foo=1")
        # Find second -D
        idx_bar = argv.index("-D", idx_foo + 1)
        self.assertEqual(argv[idx_bar + 1], "bar=2")

    def test_color_scheme(self):
        argv = self._argv(color_scheme="Tomorrow Night")
        self.assertIn("--colorscheme=Tomorrow Night", argv)

    def test_no_color_scheme_by_default(self):
        argv = self._argv()
        self.assertFalse(any("colorscheme" in a for a in argv))

    def test_output_in_argv(self):
        argv = self._argv(output=pathlib.Path("/tmp/my.png"))
        self.assertIn("-o", argv)
        self.assertIn("/tmp/my.png", argv)

    def test_scad_file_last(self):
        argv = self._argv(scad_file=pathlib.Path("my dir/part.scad"))
        self.assertEqual(argv[-1], "my dir/part.scad")

    def test_scad_path_with_space_is_single_element(self):
        argv = self._argv(scad_file=pathlib.Path("path with spaces/part.scad"))
        # The path must be one element, not split on space
        self.assertIn("path with spaces/part.scad", argv)
        self.assertNotIn("path", argv[:-1])  # "path" alone shouldn't appear

    def test_projection_override(self):
        argv = self._argv(view="top", projection="perspective")
        self.assertIn("--projection=perspective", argv)
        self.assertNotIn("--projection=ortho", argv)


class TestArgParsing(unittest.TestCase):

    def test_camera_implies_view_custom(self):
        args = parse_args(["test.scad", "--camera=0,0,0,45,0,0,500"])
        self.assertEqual(args.view, "custom")

    def test_custom_view_without_camera_raises(self):
        with self.assertRaises(SystemExit):
            parse_args(["test.scad", "--view", "custom"])

    def test_camera_with_explicit_view_non_custom_raises(self):
        with self.assertRaises(SystemExit):
            parse_args(["test.scad", "--view", "top", "--camera=0,0,0,0,0,0,500"])

    def test_camera_with_iso_view_raises(self):
        with self.assertRaises(SystemExit):
            parse_args(["test.scad", "--view", "iso", "--camera=0,0,0,0,0,0,500"])

    def test_camera_with_custom_view_ok(self):
        args = parse_args(["test.scad", "--view", "custom", "--camera=0,0,0,0,0,0,500"])
        self.assertEqual(args.view, "custom")
        self.assertEqual(args.camera, "0,0,0,0,0,0,500")

    def test_no_viewall_flag(self):
        args = parse_args(["test.scad", "--no-viewall"])
        self.assertFalse(args.viewall)

    def test_no_autocenter_flag(self):
        args = parse_args(["test.scad", "--no-autocenter"])
        self.assertFalse(args.autocenter)

    def test_y_up_flag(self):
        args = parse_args(["test.scad", "--y-up", "--view", "top"])
        self.assertTrue(args.y_up)
        self.assertEqual(args.view, "top")

    def test_defines_accumulate(self):
        args = parse_args(["test.scad", "-D", "a=1", "-D", "b=2"])
        self.assertEqual(args.defines, ["a=1", "b=2"])


class TestOutputDefault(unittest.TestCase):

    def test_parse_args_output_defaults_to_none(self):
        self.assertIsNone(parse_args(["test.scad"]).output)

    def test_parse_args_creates_no_temp_dir(self):
        with mock.patch("render_view.tempfile.mkdtemp") as m:
            parse_args(["test.scad"])
            m.assert_not_called()

    def test_explicit_output_returned_unchanged(self):
        with mock.patch("render_view.tempfile.mkdtemp") as m:
            path, tmp = resolve_output_path(pathlib.Path("/tmp/my.png"), pathlib.Path("a.scad"))
            self.assertEqual(path, pathlib.Path("/tmp/my.png"))
            self.assertIsNone(tmp)
            m.assert_not_called()

    def test_default_output_is_private_and_unique(self):
        path1, tmp1 = resolve_output_path(None, pathlib.Path("power-workshop/drill_socket.scad"))
        self.addCleanup(shutil.rmtree, str(tmp1), True)
        path2, tmp2 = resolve_output_path(None, pathlib.Path("power-workshop/drill_socket.scad"))
        self.addCleanup(shutil.rmtree, str(tmp2), True)

        self.assertNotEqual(path1, path2)
        self.assertNotEqual(tmp1, tmp2)
        self.assertEqual(path1.name, "drill_socket.png")
        self.assertEqual(path2.name, "drill_socket.png")
        self.assertEqual(path1.parent, tmp1)
        self.assertEqual(path2.parent, tmp2)
        self.assertEqual(stat.S_IMODE(os.stat(tmp1).st_mode), 0o700)
        self.assertEqual(stat.S_IMODE(os.stat(tmp2).st_mode), 0o700)

    def test_default_output_is_not_the_old_constant(self):
        path, tmp = resolve_output_path(None, pathlib.Path("test.scad"))
        self.addCleanup(shutil.rmtree, str(tmp), True)

        self.assertNotEqual(str(path), "/tmp/render.png")
        self.assertNotEqual(path.parent, pathlib.Path(tempfile.gettempdir()))

    def test_default_output_sanitizes_stem(self):
        path, tmp = resolve_output_path(None, pathlib.Path("weird name$;.scad"))
        self.addCleanup(shutil.rmtree, str(tmp), True)

        self.assertEqual(path.name, "weird name__.png")

    def test_default_output_dot_only_stem_falls_back(self):
        path, tmp = resolve_output_path(None, pathlib.Path(".."))
        self.addCleanup(shutil.rmtree, str(tmp), True)

        self.assertEqual(path.name, "render.png")


if __name__ == "__main__":
    unittest.main()
