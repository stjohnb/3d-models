"""Regression tests for _load_filament_colors_js in generate-standalone.py."""

import html as html_mod
import importlib.util
import json
import os
import sys
import unittest


def _load_module():
    scripts_dir = os.path.dirname(__file__)
    spec = importlib.util.spec_from_file_location(
        "generate_standalone",
        os.path.join(scripts_dir, "generate-standalone.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gs = _load_module()


def _write_colors(tmp_path, colors):
    path = os.path.join(tmp_path, "filament-colors.json")
    with open(path, "w") as f:
        json.dump(colors, f)
    return path


class TestLoadFilamentColorsJs(unittest.TestCase):
    def setUp(self):
        import tempfile
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._orig = gs.FILAMENT_COLORS_JSON

    def tearDown(self):
        gs.FILAMENT_COLORS_JSON = self._orig

    def _set_colors(self, colors):
        path = _write_colors(self._tmp.name, colors)
        gs.FILAMENT_COLORS_JSON = path

    def test_escapes_script_close_tag(self):
        self._set_colors([{"name": "Red</script><x>", "hex": "ff0000"}])
        result = gs._load_filament_colors_js()
        self.assertNotIn("</script>", result)
        self.assertIn("\\u003c/script\\u003e", result)

    def test_escapes_ampersand_and_gt(self):
        self._set_colors([{"name": "A&B>C", "hex": "aabbcc"}])
        result = gs._load_filament_colors_js()
        self.assertIn("\\u0026", result)
        self.assertIn("\\u003e", result)
        self.assertNotIn('"A&', result)
        self.assertNotIn('B>', result)

    def test_escapes_quotes_and_backslash(self):
        self._set_colors([{"name": 'He said "hi" \\ bye', "hex": "112233"}])
        result = gs._load_filament_colors_js()
        # The emitted entry should be valid — no unescaped double-quote breaks the JS string
        self.assertIn('\\"hi\\"', result)
        self.assertIn('\\\\', result)

    def test_rejects_control_chars(self):
        self._set_colors([{"name": "bad\x01name", "hex": "123456"}])
        with self.assertRaises(ValueError):
            gs._load_filament_colors_js()

    def test_rejects_invalid_hex(self):
        self._set_colors([{"name": "Blue", "hex": "zzzzzz"}])
        with self.assertRaises(ValueError):
            gs._load_filament_colors_js()

    def test_normal_names_unchanged(self):
        self._set_colors([{"name": "Blue", "hex": "64b5f6"}])
        result = gs._load_filament_colors_js()
        self.assertIn('      { name: "Blue", hex: 0x64b5f6 }', result)


class TestHtmlTemplateFormat(unittest.TestCase):
    """Exercise HTML_TEMPLATE.format() so a stray unescaped brace fails loudly.

    The filament-color tests above never call .format(), so without this an
    undoubled `{`/`}` in the injected JS/CSS would pass CI silently and only
    surface at build time.
    """

    def _render(self):
        return gs.HTML_TEMPLATE.format(
            title="Test Model",
            three_uri="data:text/javascript;base64,AAAA",
            stlloader_uri="data:text/javascript;base64,BBBB",
            orbitcontrols_uri="data:text/javascript;base64,CCCC",
            trackballcontrols_uri="data:text/javascript;base64,DDDD",
            arcballcontrols_uri="data:text/javascript;base64,EEEE",
            stl_base64="ZmFrZQ==",
            filament_colors_js='[\n      { name: "Blue", hex: 0x64b5f6 },\n    ]',
        )

    def test_format_succeeds_and_includes_controls(self):
        html = self._render()
        # Control-mode buttons and rotate buttons are present
        self.assertIn('id="mode-orbit"', html)
        self.assertIn('id="mode-trackball"', html)
        self.assertIn('id="mode-arcball"', html)
        self.assertIn('id="rot-x"', html)
        self.assertIn('id="rot-y"', html)
        self.assertIn('id="rot-z"', html)
        self.assertIn('id="reset-view"', html)
        # Only orbit starts pressed
        self.assertIn('id="mode-orbit" aria-label="Use Orbit controls" aria-pressed="true"', html)
        self.assertIn('id="mode-trackball" aria-label="Use Trackball controls" aria-pressed="false"', html)
        self.assertIn('id="mode-arcball" aria-label="Use Arcball controls" aria-pressed="false"', html)
        # The new control libraries are wired into the importmap and imports
        self.assertIn('TrackballControls.js', html)
        self.assertIn('ArcballControls.js', html)
        # Placeholders were substituted, not left literal
        self.assertNotIn('{three_uri}', html)
        self.assertIn('data:text/javascript;base64,DDDD', html)
        self.assertIn('data:text/javascript;base64,EEEE', html)
        # Key JS functions survive template formatting
        self.assertIn('function makeControls(', html)
        self.assertIn('function rotateMesh(', html)
        self.assertIn('function recomputeClip(', html)

    def test_title_html_escaping(self):
        html = gs.HTML_TEMPLATE.format(
            title=html_mod.escape('Evil <script>alert(1)</script>'),
            three_uri="data:text/javascript;base64,AAAA",
            stlloader_uri="data:text/javascript;base64,BBBB",
            orbitcontrols_uri="data:text/javascript;base64,CCCC",
            trackballcontrols_uri="data:text/javascript;base64,DDDD",
            arcballcontrols_uri="data:text/javascript;base64,EEEE",
            stl_base64="ZmFrZQ==",
            filament_colors_js='[\n      { name: "Blue", hex: 0x64b5f6 },\n    ]',
        )
        self.assertIn('&lt;script&gt;', html)
        self.assertNotIn('<script>alert(1)</script>', html)


if __name__ == "__main__":
    unittest.main()
