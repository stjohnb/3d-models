"""Pins the relieved-plate geometry from issue #492.

The fixing plate is thin (relief_t) over the bottom relief_h mm, where the
drawer face meets the front edge of the cabinet's bottom panel — that band is
the only part of the bracket holding the drawer front proud when closed.
Above it the plate stays full thickness (rear_t) for stiffness and screw
purchase, and the screw heads are not countersunk since nothing in the
cabinet backs onto them at that height.

Run with: python3 -m unittest test_bin_foot_opener
"""

import itertools
import json
import pathlib
import re
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PROJECT_DIR = REPO_ROOT / "bin-foot-opener"


def source():
    return (PROJECT_DIR / "bin_foot_pull.scad").read_text(encoding="utf-8")


def scad_number(name):
    match = re.search(rf"^{name}\s*=\s*([0-9.]+)\s*;", source(), re.M)
    if match is None:
        raise AssertionError(f"{name} not found in bin_foot_pull.scad")
    return float(match.group(1))


def manifest():
    return json.loads(
        (PROJECT_DIR / "bin_foot_pull.parameters.json").read_text(encoding="utf-8")
    )


class BinFootOpenerTests(unittest.TestCase):
    def test_relief_band_is_thin(self):
        self.assertEqual(scad_number("relief_h"), 22.0)
        self.assertEqual(scad_number("relief_t"), 1.6)
        self.assertLessEqual(scad_number("relief_t"), scad_number("rear_t") - 1)

    def test_screws_are_not_countersunk(self):
        self.assertNotIn("csk_depth", source())
        self.assertNotIn("d1 =", source())

    def test_manifest_covers_the_relief_parameters(self):
        entries = {e["name"]: e for e in manifest()["parameters"]}
        for name in ("relief_h", "relief_t"):
            self.assertIn(name, entries)
            self.assertEqual(entries[name]["type"], "number")

    def test_manifest_defaults_match_the_source(self):
        for entry in manifest()["parameters"]:
            if entry["type"] != "number":
                continue
            self.assertAlmostEqual(
                scad_number(entry["name"]), entry["default"], places=6
            )

    def test_manifest_defaults_are_in_range(self):
        for entry in manifest()["parameters"]:
            if entry["type"] == "number":
                self.assertLessEqual(entry["min"], entry["default"])
                self.assertLessEqual(entry["default"], entry["max"])
            elif entry["type"] == "boolean":
                self.assertIsInstance(entry["default"], bool)

    def test_manifest_extremes_leave_room_for_both_screw_rows(self):
        # Mirrors the screw_y_lo/screw_y_hi derivation in bin_foot_pull.scad:
        # every corner of the relief_h x rear_t x relief_t x rear_h manifold
        # must still satisfy the "screw rows too close together" assert, not
        # just the shipped defaults (issue #492 review, PR #495).
        screw_head_d = scad_number("screw_head_d")
        entries = {e["name"]: e for e in manifest()["parameters"]}
        corners = itertools.product(
            (entries["relief_h"]["min"], entries["relief_h"]["max"]),
            (entries["rear_t"]["min"], entries["rear_t"]["max"]),
            (entries["relief_t"]["min"], entries["relief_t"]["max"]),
            (entries["rear_h"]["min"], entries["rear_h"]["max"]),
        )
        for relief_h, rear_t, relief_t, rear_h in corners:
            if rear_t - relief_t < 1:
                continue  # already rejected by the rear_t/relief_t assert
            with self.subTest(
                relief_h=relief_h, rear_t=rear_t, relief_t=relief_t, rear_h=rear_h
            ):
                relief_top = relief_h + rear_t - relief_t if relief_h > 0 else 0
                screw_y_lo = max(relief_top + screw_head_d / 2 + 3, 20)
                screw_y_hi = rear_h - screw_head_d / 2 - 4
                self.assertGreaterEqual(rear_h - screw_y_hi, screw_head_d / 2 + 2)
                self.assertGreaterEqual(
                    screw_y_lo - screw_head_d / 2, relief_top + 1.5
                )
                self.assertGreaterEqual(screw_y_hi - screw_y_lo, screw_head_d + 2)


if __name__ == "__main__":
    unittest.main()
