"""Pins the resistor-storage-box customizer manifests against the library.

Run with: python3 -m unittest test_resistor_storage_box
"""

import json
import pathlib
import re
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PROJECT_DIR = REPO_ROOT / "resistor-storage-box"
LIBRARY = PROJECT_DIR / "_resistor_storage_box.scad"
MANIFESTS = (
    PROJECT_DIR / "resistor_box.parameters.json",
    PROJECT_DIR / "resistor_box_lid.parameters.json",
)


def source():
    return LIBRARY.read_text(encoding="utf-8")


def scad_value(name):
    match = re.search(rf"^{name}\s*=\s*([^;]+);", source(), re.M)
    if match is None:
        raise AssertionError(f"{name} not found in {LIBRARY.name}")
    return match.group(1).strip()


def scad_number(name):
    return float(scad_value(name))


class ResistorStorageBoxTests(unittest.TestCase):
    def test_manifests_match_the_library(self):
        for path in MANIFESTS:
            for entry in json.loads(path.read_text(encoding="utf-8"))["parameters"]:
                with self.subTest(manifest=path.name, name=entry["name"]):
                    value = scad_value(entry["name"])
                    if entry["type"] == "boolean":
                        self.assertEqual(value, str(entry["default"]).lower())
                    else:
                        self.assertAlmostEqual(float(value), entry["default"])
                        self.assertLessEqual(entry["min"], entry["default"])
                        self.assertLessEqual(entry["default"], entry["max"])

    def test_manifests_share_the_box_size(self):
        names = [
            {e["name"] for e in json.loads(p.read_text(encoding="utf-8"))["parameters"]}
            for p in MANIFESTS
        ]
        for name in ("outer_l", "outer_w", "wall", "corner_r"):
            for manifest in names:
                self.assertIn(name, manifest)

    def test_default_envelope_matches_the_issue(self):
        self.assertEqual(scad_number("outer_l"), 100)
        self.assertEqual(scad_number("outer_w"), 70)
        self.assertEqual(scad_number("outer_h"), 70)


if __name__ == "__main__":
    unittest.main()
