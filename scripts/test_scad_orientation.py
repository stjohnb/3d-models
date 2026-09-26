"""Pins the single-orientation rule for `.scad` sources (issue #382).

Every source in this repo stays in OpenSCAD's native Z-up coordinates, so the
PNG thumbnails CI renders with OpenSCAD's default (Z-up) camera and the STLs
users download for slicing are both correct. The Z-up -> Y-up conversion the
Three.js viewers need is applied unconditionally by the viewers themselves
(`index.html`, `embed.html`, `scripts/generate-standalone.py`), never by a
source-level `rotate([-90, 0, 0])`.

Run with: python3 -m unittest test_scad_orientation
"""

import pathlib
import re
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# The one top-level rotate([-90, 0, 0]) that is a genuine *print* orientation:
# toothbrush_backplate() stands upright in the library and this file lays it on
# its back, flat on the bed.
ALLOWED_TOP_LEVEL_ROTATE_X = {"toothbrush/Toothbrush backplate.scad"}

# Column 0 only — an indented rotate([-90, 0, 0]) is interior geometry.
TOP_LEVEL_ROTATE_X = re.compile(r"^rotate\(\[\s*-90\s*,\s*0\s*,\s*0\s*\]\)")


def scad_sources():
    for path in sorted(REPO_ROOT.rglob("*.scad")):
        if ".git" in path.parts:
            continue
        yield path


class ScadOrientationTests(unittest.TestCase):
    def test_no_top_level_viewer_rotation(self):
        offenders = []
        for path in scad_sources():
            rel = path.relative_to(REPO_ROOT).as_posix()
            if rel in ALLOWED_TOP_LEVEL_ROTATE_X:
                continue
            lines = path.read_text(encoding="utf-8").splitlines()
            for lineno, line in enumerate(lines, start=1):
                if TOP_LEVEL_ROTATE_X.match(line):
                    offenders.append(f"{rel}:{lineno}")
        self.assertEqual(
            offenders,
            [],
            "top-level rotate([-90, 0, 0]) found in "
            + ", ".join(offenders)
            + " — sources stay OpenSCAD Z-up; the viewers apply the Z-up -> "
            "Y-up conversion to every mesh themselves, so a source rotate "
            "tips the thumbnail and the printed part over instead",
        )

    def test_allowlisted_files_exist(self):
        for rel in sorted(ALLOWED_TOP_LEVEL_ROTATE_X):
            self.assertTrue(
                (REPO_ROOT / rel).is_file(),
                f"{rel} is allowlisted for a top-level rotate([-90, 0, 0]) but "
                "no longer exists — update ALLOWED_TOP_LEVEL_ROTATE_X",
            )


if __name__ == "__main__":
    unittest.main()
