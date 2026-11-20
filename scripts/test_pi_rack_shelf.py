"""Pins the pi-rack-shelf dimensions and customizer manifests to the library.

The measured Pi cases and the 19-inch rack width are fixed by the issue,
every half must fit a 256 mm A1 bed, the manifests must agree with the
library's defaults, and every corner of their ranges must pass the library's
layout asserts.

Run with: python3 -m unittest test_pi_rack_shelf
"""

import itertools
import json
import math
import pathlib
import re
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PROJECT_DIR = REPO_ROOT / "pi-rack-shelf"
LIBRARY = PROJECT_DIR / "_pi_rack_shelf.scad"
PARTS = (
    "pi_rack_shelf_2u_pi",
    "pi_rack_shelf_2u_tray",
)
MANIFESTS = tuple(PROJECT_DIR / f"{part}.parameters.json" for part in PARTS)
A1_LIMIT = 250


def source():
    return LIBRARY.read_text(encoding="utf-8")


def scad_value(name):
    match = re.search(rf"^{name}\s*=\s*([^;]+);", source(), re.M)
    if match is None:
        raise AssertionError(f"{name} not found in {LIBRARY.name}")
    return match.group(1).strip()


def scad_number(name):
    return float(scad_value(name))


def to_python(expr):
    expr = expr.replace("&&", " and ")
    expr = re.sub(r"\btrue\b", "True", expr)
    return re.sub(r"\bfalse\b", "False", expr)


def library_program():
    """Top-level assignments and assert conditions, compiled as Python."""
    text = re.sub(r"//[^\n]*", "", source())
    assignments = [
        (name, compile(to_python(expr), name, "eval"))
        for name, expr in re.findall(r"^([A-Za-z_]\w*)\s*=\s*([^;]+);", text, re.M)
    ]
    asserts = [
        (message, compile(f"({to_python(cond)})", message, "eval"))
        for cond, message in re.findall(
            r'^assert\((.*?),\s*"([^"]*)"\);', text, re.M | re.S
        )
    ]
    return assignments, asserts


def evaluate(program, overrides):
    """Evaluates like openscad -D: an override replaces its assignment."""
    assignments, asserts = program
    env = {"min": min, "max": max, "abs": abs}
    # The library's functions used by its derived values and asserts.
    env["cos"] = lambda deg: math.cos(math.radians(deg))
    for name, code in assignments:
        env[name] = overrides[name] if name in overrides else eval(code, env)
    return env, [message for message, code in asserts if not eval(code, env)]


def failed_asserts(program, overrides):
    return evaluate(program, overrides)[1]


class PiRackShelfTests(unittest.TestCase):
    def test_every_part_has_a_renderable_and_manifest(self):
        for part in PARTS:
            with self.subTest(part=part):
                scad = (PROJECT_DIR / f"{part}.scad").read_text(encoding="utf-8")
                self.assertIn("include <_pi_rack_shelf.scad>", scad)
                self.assertTrue((PROJECT_DIR / f"{part}.parameters.json").is_file())

    def test_generic_pi_case(self):
        self.assertEqual(scad_number("pi_case_w"), 66)
        self.assertEqual(scad_number("pi_case_h"), 30)
        self.assertEqual(scad_number("pi_d"), 94)
        self.assertEqual(scad_number("pi_fit"), 0.5)
        self.assertEqual(scad_number("pi_count"), 4)
        self.assertEqual(scad_number("min_air_gap"), 10)
        self.assertEqual(scad_number("min_headroom"), 15)
        self.assertEqual(scad_number("box_wall_h"), 40)
        self.assertEqual(scad_number("sd_gap"), 30)
        self.assertEqual(scad_number("fin_h"), 25)

    def test_1u_and_cable_clearance_are_gone(self):
        text = source()
        for name in ("1u", "cable_clearance", "pi_a_w", "pi_b_w"):
            self.assertNotIn(name, text)

    def test_rack_standard(self):
        self.assertEqual(scad_number("rack_panel_w"), 482.6)
        self.assertEqual(scad_number("rack_hole_span"), 465.1)
        self.assertEqual(scad_number("rack_u"), 44.45)
        self.assertGreater(scad_number("panel_clearance"), 0)

    def test_halves_split_at_the_centre_and_fit_the_a1_bed(self):
        self.assertEqual(scad_number("split_x"), 0)
        half = scad_number("rack_panel_w") / 2
        self.assertAlmostEqual(half, 241.3)
        self.assertLessEqual(half, A1_LIMIT)
        self.assertLessEqual(scad_number("depth"), A1_LIMIT)

    def test_defaults_pass_the_asserts(self):
        env, failures = evaluate(library_program(), {})
        self.assertEqual(failures, [])
        self.assertGreaterEqual(env["air_gap"], 10)
        self.assertAlmostEqual(env["headroom"], 19.1, places=1)

    def test_headroom_assert_fails_for_a_taller_case(self):
        failures = failed_asserts(library_program(), {"pi_case_w": 72})
        self.assertIn("headroom above the Pis below min_headroom", failures)

    def test_too_many_pis_fail_the_air_gap_assert(self):
        failures = failed_asserts(library_program(), {"pi_count": 6})
        self.assertIn("air gap around the Pi slots below min_air_gap or bolt_head_clear", failures)

    def test_pi_count_is_range_checked_and_one_pi_is_centred(self):
        program = library_program()
        for count in (0, 5):
            with self.subTest(pi_count=count):
                self.assertIn(
                    "pi_count must be 1 to 4", failed_asserts(program, {"pi_count": count})
                )
        env, failures = evaluate(program, {"pi_count": 1})
        self.assertEqual(failures, [])
        # One Pi: equal gaps either side of the single cell
        self.assertTrue(math.isfinite(env["air_gap"]))
        self.assertAlmostEqual(
            env["air_gap"], (env["x_in1"] - env["x_in0"] - env["cell_w"]) / 2
        )

    def test_end_gaps_equal_gaps_between_slots(self):
        env, _ = evaluate(library_program(), {})
        n = env["pi_count"]
        used = n * env["cell_w"] + (n + 1) * env["air_gap"]
        self.assertAlmostEqual(used, env["x_in1"] - env["x_in0"])

    def test_rear_nut_trap_clears_the_floor_at_every_range_end(self):
        program = library_program()
        for floor in (2, 4):
            for h in (36, 60):
                self.assertEqual(
                    failed_asserts(program, {"floor_t": floor, "box_wall_h": h}), []
                )

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

    def test_manifest_range_corners_pass_the_asserts(self):
        # Every combination of all parameters at their range ends
        program = library_program()
        for path in MANIFESTS:
            ends = []
            for entry in json.loads(path.read_text(encoding="utf-8"))["parameters"]:
                if entry["type"] == "boolean":
                    values = (False, True)
                else:
                    values = (entry["min"], entry["max"])
                ends.append([(entry["name"], v) for v in values])
            for combo in itertools.product(*ends):
                failures = failed_asserts(program, dict(combo))
                self.assertEqual(failures, [], f"{path.name}: {dict(combo)}")

    def test_range_limits_are_tight(self):
        # Each range end that an assert bounds is the last value that
        # passes: one step beyond it must fail, so the manifest cannot drift.
        program = library_program()
        worst_floor = {"floor_t": 4}
        self.assertTrue(failed_asserts(program, {"window_inset": 3.5, "pi_fit": 0.2}))
        self.assertEqual(failed_asserts(program, {"window_inset": 3, "pi_fit": 0.2}), [])
        self.assertTrue(failed_asserts(program, {**worst_floor, "box_wall_h": 35}))
        self.assertEqual(failed_asserts(program, {**worst_floor, "box_wall_h": 36}), [])

    def test_box_wall_h_manifest_minimum_is_the_smallest_passing_value(self):
        # The manifest minimum must be the smallest value that passes at the
        # thickest floor the manifests allow, so the customizer's low end
        # cannot break the build.
        program = library_program()
        for part in ("pi_rack_shelf_2u_pi", "pi_rack_shelf_2u_tray"):
            entries = {
                e["name"]: e
                for e in json.loads(
                    (PROJECT_DIR / f"{part}.parameters.json").read_text(encoding="utf-8")
                )["parameters"]
            }
            low = entries["box_wall_h"]["min"]
            floor = {"floor_t": entries["floor_t"]["max"]}
            with self.subTest(part=part):
                self.assertEqual(failed_asserts(program, {**floor, "box_wall_h": low}), [])
                self.assertTrue(
                    failed_asserts(program, {**floor, "box_wall_h": low - 1})
                )

if __name__ == "__main__":
    unittest.main()
