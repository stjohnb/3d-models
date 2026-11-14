"""Customizer ranges for desk-armrest must never trip the SCAD asserts."""
import itertools
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "desk-armrest"


class DeskArmrestRanges(unittest.TestCase):
    def setUp(self):
        params = json.loads((ROOT / "desk_armrest.parameters.json").read_text())
        self.p = {x["name"]: x for x in params["parameters"]}

    def test_asserts_hold_at_range_extremes(self):
        names = ["desk_t", "fit_clearance", "jaw_t", "pad_t", "arm_root_t", "arm_tip_t", "reach"]
        spine_t, lead_in, edge_r = 10, 3, 2
        for combo in itertools.product(*[(self.p[n]["min"], self.p[n]["max"]) for n in names]):
            v = dict(zip(names, combo))
            z_top = v["jaw_t"] + v["desk_t"] + v["fit_clearance"] + v["pad_t"]
            self.assertLess(spine_t, v["reach"])
            self.assertLessEqual(v["arm_tip_t"], v["arm_root_t"], v)
            self.assertLess(v["arm_root_t"], z_top, v)
            self.assertLess(lead_in, min(v["jaw_t"], v["pad_t"]))
            self.assertLess(2 * edge_r, min(v["jaw_t"], v["pad_t"], v["arm_tip_t"], spine_t))

    def test_defaults_match_scad(self):
        src = (ROOT / "desk_armrest.scad").read_text()
        for name, p in self.p.items():
            self.assertRegex(src, rf"(?m)^{name}\s*=\s*{p['default']}\s*;")


if __name__ == "__main__":
    unittest.main()
