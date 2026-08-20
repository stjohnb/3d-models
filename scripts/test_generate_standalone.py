"""Regression tests for _load_filament_colors_js and the SEO head fields
(_seo_fields) in generate-standalone.py."""

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

    def _render(self, **overrides):
        kwargs = dict(
            title="Test Model",
            three_uri="data:text/javascript;base64,AAAA",
            stlloader_uri="data:text/javascript;base64,BBBB",
            orbitcontrols_uri="data:text/javascript;base64,CCCC",
            stl_base64="ZmFrZQ==",
            filament_colors_js='[\n      { name: "Blue", hex: 0x64b5f6 },\n    ]',
            composite_parts_js="[]",
            source_link_html="",
            printing_notes_html="",
            meta_description="A test model",
            canonical_url="https://www.bstjohn.net/3d-models/standalone/test.html",
            thumbnail_url="https://www.bstjohn.net/3d-models/test.png",
            structured_data='{"@type":"3DModel"}',
        )
        kwargs.update(overrides)
        return gs.HTML_TEMPLATE.format(**kwargs)

    def test_format_succeeds_and_includes_controls(self):
        html = self._render()
        # Rotate/reset/cross-section controls are present
        self.assertIn('id="rot-x"', html)
        self.assertIn('id="rot-y"', html)
        self.assertIn('id="rot-z"', html)
        self.assertIn('id="reset-view"', html)
        self.assertIn('id="cross-btn"', html)
        self.assertIn('id="clip-slider"', html)
        # Issue #337: the Orbit/Trackball/Arcball switcher is gone — controls
        # are always OrbitControls, so those modules aren't embedded either.
        self.assertNotIn('id="mode-orbit"', html)
        self.assertNotIn('id="mode-trackball"', html)
        self.assertNotIn('id="mode-arcball"', html)
        self.assertNotIn('TrackballControls.js', html)
        self.assertNotIn('ArcballControls.js', html)
        # Issue #337: cross-section and view buttons share one row
        self.assertNotIn('cross-section-row', html)
        # Placeholders were substituted, not left literal
        self.assertNotIn('{three_uri}', html)
        # Key JS functions survive template formatting
        self.assertIn('function makeControls(', html)
        self.assertIn('function rotateMesh(', html)
        self.assertIn('function recomputeClip(', html)

    def test_title_html_escaping(self):
        html = self._render(title=html_mod.escape('Evil <script>alert(1)</script>'))
        self.assertIn('&lt;script&gt;', html)
        self.assertNotIn('<script>alert(1)</script>', html)

    def test_format_succeeds(self):
        """The new {composite_parts_js} placeholder is substituted, not left literal."""
        html = self._render()
        self.assertIn('const COMPOSITE_PARTS = [];', html)
        self.assertNotIn('{composite_parts_js}', html)


class TestCompositePartsJs(unittest.TestCase):
    """_js_escape / _composite_parts_js must neutralise <, >, & in embedded data."""

    def test_js_escape_neutralises_script_break(self):
        result = gs._js_escape('</script>&<x>')
        self.assertNotIn('<', result)
        self.assertNotIn('>', result)
        self.assertNotIn('&', result)
        self.assertIn('\\u003c', result)
        self.assertIn('\\u003e', result)
        self.assertIn('\\u0026', result)

    def test_composite_parts_js_escapes_crafted_payload(self):
        parts = [{"stl_b64": "AAAA</script>&<", "color": "#64b5f6"}]
        result = gs._composite_parts_js(parts)
        self.assertNotIn('<', result)
        self.assertNotIn('>', result)
        self.assertNotIn('&', result)
        self.assertIn('\\u003c', result)

    def test_composite_parts_js_valid_part_round_trips(self):
        parts = [{"stl_b64": "AAAA", "color": "#64b5f6"}]
        result = gs._composite_parts_js(parts)
        self.assertIn('#64b5f6', result)
        # No escapable characters, so it stays valid JSON.
        self.assertEqual(json.loads(result), parts)


class TestSeoFields(unittest.TestCase):
    """_seo_fields must build correct URLs/JSON-LD and escape crafted input."""

    def test_uses_meta_description(self):
        result = gs._seo_fields("drill_bit.stl", "drill bit", {"description": "A bit."})
        self.assertEqual(result["meta_description"], "A bit.")
        self.assertEqual(json.loads(result["structured_data"])["description"], "A bit.")

    def test_falls_back_when_description_missing(self):
        for meta in ({}, {"description": "   "}, {"description": 123}):
            result = gs._seo_fields("drill_bit.stl", "drill bit", meta)
            self.assertIn("3D printable drill bit", result["meta_description"])

    def test_canonical_and_thumbnail_urls(self):
        result = gs._seo_fields("drill_bit.stl", "drill bit", {})
        self.assertEqual(
            result["canonical_url"],
            "https://www.bstjohn.net/3d-models/standalone/drill_bit.html",
        )
        self.assertEqual(
            result["thumbnail_url"],
            "https://www.bstjohn.net/3d-models/drill_bit.png",
        )

    def test_space_in_filename_is_percent_encoded(self):
        result = gs._seo_fields("Toothbrush assembly.stl", "toothbrush assembly", {})
        self.assertIn("%20", result["canonical_url"])
        self.assertIn("%20", result["thumbnail_url"])
        self.assertNotIn(" ", result["canonical_url"])
        self.assertNotIn(" ", result["thumbnail_url"])

    def test_jsonld_shape(self):
        result = gs._seo_fields("drill_bit.stl", "drill bit", {})
        data = json.loads(result["structured_data"])
        self.assertEqual(data["@type"], "3DModel")
        self.assertEqual(data["encodingFormat"], "model/stl")
        self.assertTrue(data["contentUrl"].endswith("/drill_bit.stl"))
        self.assertTrue(data["@id"].endswith(".html#model"))
        self.assertEqual(
            data["isPartOf"]["@id"], "https://www.bstjohn.net/3d-models/#collection"
        )
        self.assertEqual(data["name"], "Drill Bit")

    def test_escapes_crafted_description(self):
        payload = '</script><script>alert(1)</script> "quoted" & <b>'
        result = gs._seo_fields("drill_bit.stl", "drill bit", {"description": payload})

        self.assertNotIn('</script>', result["structured_data"])
        self.assertNotIn('<', result["structured_data"])
        self.assertIn('\\u003c', result["structured_data"])
        self.assertEqual(json.loads(result["structured_data"])["description"], payload)

        self.assertNotIn('"', result["meta_description"])
        self.assertNotIn('<', result["meta_description"])
        self.assertIn('&quot;', result["meta_description"])

    def test_rendered_page_contains_no_script_break(self):
        seo = gs._seo_fields("x.stl", "x", {"description": '</script><img src=x>'})
        html = TestHtmlTemplateFormat()._render(
            structured_data=seo["structured_data"],
            meta_description=seo["meta_description"],
        )
        self.assertNotIn('</script><img', html)
        self.assertNotIn('<img src=x>', html)


class TestSourceLinkHtml(unittest.TestCase):
    """_source_link_html must link to the public mirror and escape safely."""

    def test_basic_link(self):
        result = gs._source_link_html("power-workshop/drill_bit.scad")
        self.assertIn(
            "https://github.com/stjohnb/3d-models/blob/main/power-workshop/drill_bit.scad",
            result,
        )
        self.assertIn('target="_blank"', result)
        self.assertIn('rel="noopener noreferrer"', result)

    def test_space_in_path_segment(self):
        result = gs._source_link_html("toothbrush/Toothbrush assembly.scad")
        self.assertIn("Toothbrush%20assembly.scad", result)
        href_start = result.index('href="') + len('href="')
        href_end = result.index('"', href_start)
        self.assertNotIn(" ", result[href_start:href_end])

    def test_empty_source(self):
        self.assertEqual(gs._source_link_html(""), "")

    def test_escapes_crafted_payload(self):
        result = gs._source_link_html('a/b"c<d&e.scad')
        href_start = result.index('href="') + len('href="')
        href_end = result.index('"', href_start)
        href = result[href_start:href_end]
        self.assertNotIn('"', href)
        self.assertNotIn('<', href)
        self.assertNotIn('&', href)


class TestPrintingNotesHtml(unittest.TestCase):
    """_printing_notes_html must escape free-text notes and skip invalid entries."""

    def test_escapes_html(self):
        result = gs._printing_notes_html(['<img src=x onerror=alert(1)>'])
        self.assertIn('&lt;img', result)
        self.assertNotIn('<img', result)

    def test_escapes_quotes_and_ampersand(self):
        result = gs._printing_notes_html(['A & B "quoted"'])
        self.assertIn('&amp;', result)
        self.assertIn('&quot;', result)
        self.assertNotIn('A & B', result)

    def test_returns_empty_for_none(self):
        self.assertEqual(gs._printing_notes_html(None), "")

    def test_returns_empty_for_non_list(self):
        self.assertEqual(gs._printing_notes_html("a string"), "")

    def test_returns_empty_for_blank_entries(self):
        self.assertEqual(gs._printing_notes_html(["", "   "]), "")

    def test_skips_non_string_entries(self):
        result = gs._printing_notes_html([123, "real note"])
        self.assertIn('<li>real note</li>', result)
        self.assertEqual(result.count('<li>'), 1)

    def test_renders_multiple_items(self):
        result = gs._printing_notes_html(["First note", "Second note"])
        self.assertEqual(result.count('<li>'), 2)
        self.assertIn('<details class="printing-notes">', result)
        self.assertIn('<summary>Printing notes</summary>', result)


if __name__ == "__main__":
    unittest.main()
