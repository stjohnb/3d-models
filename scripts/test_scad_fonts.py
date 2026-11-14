"""Pins the no-text()/no-font rule for `.scad` sources.

The deployed openscad-wasm customizer omits the font bundle
(`scripts/fetch_openscad_wasm.py`'s `ASSET_FILES` skips the 8.1MB
`openscad.fonts.js`), so `text()` renders correctly in CI's native OpenSCAD
build but silently produces no geometry in the browser customizer. Every
`.scad` source must build glyphs from primitives instead (see
`scanning-rig/_scanning_rig.scad`'s `digit_2d`/`number_2d`).

Run with: python3 -m unittest test_scad_fonts
"""

import pathlib
import re
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

TEXT_CALL = re.compile(r"\btext\s*\(")


def scad_sources():
    for path in sorted(REPO_ROOT.rglob("*.scad")):
        if ".git" in path.parts:
            continue
        yield path


def strip_comments(source):
    without_block_comments = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"//[^\n]*", "", without_block_comments)


class ScadFontTests(unittest.TestCase):
    def test_no_scad_uses_text(self):
        offenders = []
        for path in scad_sources():
            rel = path.relative_to(REPO_ROOT).as_posix()
            stripped = strip_comments(path.read_text(encoding="utf-8"))
            if TEXT_CALL.search(stripped):
                offenders.append(rel)
        self.assertEqual(
            offenders,
            [],
            "text() found in " + ", ".join(offenders) + " — the deployed "
            "customizer's openscad-wasm build ships no font bundle, so "
            "text() renders in CI but silently vanishes in the browser; "
            "build glyphs from primitives (see "
            "_scanning_rig.scad's digit_2d)",
        )

    def test_wasm_assets_exclude_fonts(self):
        source = (REPO_ROOT / "scripts" / "fetch_openscad_wasm.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn(
            "openscad.fonts.js",
            source,
            "fetch_openscad_wasm.py now references openscad.fonts.js — if "
            "fonts are being added intentionally, this test and the "
            "no-text() rule need to be revisited together",
        )


if __name__ == "__main__":
    unittest.main()
