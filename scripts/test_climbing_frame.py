"""Pins the climbing-frame layout from issues clw_01M5CGXXBB1NEF5ZTRRGN78QF3,
clw_01M5CMH1MTPKEK6YHW1ZP3DG97 and clw_01M5CSGZJ2ZNBGSHBHE31PD9J4.

Two 94 x 145 cross beams at 0.35 and 0.65 of frame_depth carry the swings
and six monkey-bar rungs at 300 mm pitch; members take finished planed sizes.
A boarded climbing wall with holds covers the X = 0 end and a rope net on a
ground bearer covers the X = frame_x end. The monkey-bar assert in
_climbing_frame.scad must explain its limit at every corner of the
customizer ranges that feed it, not just the defaults. The *_aframe
renderables set the library switch aframe_end to swap the X = frame_x posts for
raked legs, an apex tie and a trapezoid net.

Run with: python3 -m unittest test_climbing_frame
"""

import itertools
import json
import math
import pathlib
import re
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PROJECT_DIR = REPO_ROOT / "climbing-frame"
MANIFESTS = (
    "climbing_frame",
    "climbing_slide",
    "climbing_swing",
    "climbing_net",
    "climbing_frame_aframe",
    "climbing_net_aframe",
    "climbing_assembly_aframe",
    "climbing_assembly",
)
ASSEMBLIES = ("climbing_assembly", "climbing_assembly_aframe")
NON_ASSEMBLY = tuple(m for m in MANIFESTS if m not in ASSEMBLIES)
AFRAME_RENDERABLES = (
    "climbing_frame_aframe",
    "climbing_net_aframe",
    "climbing_assembly_aframe",
)


def source():
    return (PROJECT_DIR / "_climbing_frame.scad").read_text(encoding="utf-8")


def scad_value(name):
    match = re.search(rf"(?:^|;)\s*{name}\s*=\s*([0-9.]+|true|false)\s*;", source(), re.M)
    if match is None:
        raise AssertionError(f"{name} not found in _climbing_frame.scad")
    value = match.group(1)
    if value in ("true", "false"):
        return value == "true"
    return float(value)


def layout(post=None, denom=None):
    """Mirror the library's slide-bay derivations (scad_value reads only literals)."""
    post = scad_value("post_size") if post is None else post
    denom = scad_value("scale_denominator") if denom is None else denom
    opening = scad_value("slide_opening")
    divider_c = post / 2 + post + opening
    divider_x0 = divider_c - post / 2
    divider_x1 = divider_c + post / 2
    rung_d = 1.75 * denom
    return {
        "divider_c": divider_c,
        "divider_x0": divider_x0,
        "divider_x1": divider_x1,
        "frame_x": divider_x1 + scad_value("swing_bay_clear") + post,
        "slide_x0": post + (opening - scad_value("slide_w")) / 2,
        "ladder_x0": post + (opening - scad_value("ladder_w")) / 2,
        "swing_x": [divider_x1 + 528, divider_x1 + 1203],
        "monkey_rung_start": divider_x1 + 150 + rung_d / 2,
    }


def manifest(name):
    path = PROJECT_DIR / f"{name}.parameters.json"
    entries = json.loads(path.read_text(encoding="utf-8"))["parameters"]
    return {e["name"]: e for e in entries}


def scad_range(start, step, end):
    """OpenSCAD [start : step : end], end inclusive."""
    values = []
    v = start
    while v <= end:
        values.append(v)
        v += step
    return values


def hold_xy():
    match = re.search(r"^hold_xy = (\[.*?\]\]);", source(), re.M | re.S)
    if match is None:
        raise AssertionError("hold_xy not found in _climbing_frame.scad")
    return json.loads(match.group(1))


# Default wall layout, mirroring _climbing_frame.scad.
WALL_BASE_Z = 100
WALL_BOARD_W = 94
WALL_PITCH = 100
WALL_BOARD_COUNT = 14
HOLD_H = 60


def board_centre_z(i):
    return WALL_BASE_Z + i * WALL_PITCH + WALL_BOARD_W / 2


def hold_z(z):
    # Mirrors hold_z() in _climbing_frame.scad; OpenSCAD round() is half away from zero.
    i = math.floor((z - WALL_BASE_Z) / WALL_PITCH)
    lo = WALL_BASE_Z + i * WALL_PITCH + HOLD_H / 2
    hi = WALL_BASE_Z + i * WALL_PITCH + WALL_BOARD_W - HOLD_H / 2
    if lo <= z <= hi:
        return z
    nearest = math.floor((z - WALL_BASE_Z - WALL_BOARD_W / 2) / WALL_PITCH + 0.5)
    return board_centre_z(min(WALL_BOARD_COUNT - 1, max(0, nearest)))


class ClimbingFrameTests(unittest.TestCase):
    def test_finished_timber_defaults(self):
        self.assertEqual(scad_value("post_size"), 94)
        self.assertEqual(scad_value("beam_depth"), 145)
        self.assertEqual(scad_value("corner_radius"), 5)
        self.assertEqual(scad_value("frame_depth"), 2000)
        self.assertEqual(scad_value("rung_count"), 6)
        self.assertEqual(scad_value("rung_pitch"), 300)
        self.assertEqual(scad_value("stile_w"), 44)
        self.assertEqual(scad_value("joist_w"), 45)
        self.assertEqual(scad_value("board_t"), 27)
        self.assertEqual(scad_value("board_w"), 120)

    def test_wall_and_net_defaults(self):
        self.assertEqual(scad_value("wall_board_t"), 44)
        self.assertEqual(scad_value("wall_board_w"), WALL_BOARD_W)
        self.assertEqual(scad_value("wall_base_z"), WALL_BASE_Z)
        self.assertEqual(scad_value("wall_gap"), 6)
        self.assertEqual(scad_value("hold_count"), 9)
        self.assertIs(scad_value("climbing_wall"), True)
        self.assertIs(scad_value("end_net"), True)
        self.assertEqual(scad_value("bearer_z"), 150)
        self.assertEqual(scad_value("net_width"), 1500)
        self.assertEqual(scad_value("net_mesh"), 300)

    def test_print_sized_features(self):
        self.assertRegex(source(), re.compile(r"^rung_d\s*=\s*1\.75 \* scale_denominator;", re.M))
        self.assertRegex(source(), re.compile(r"^rope_d\s*=\s*1\.4 \* scale_denominator;", re.M))

    def test_swing_positions(self):
        self.assertIn("swing_x = [divider_x1 + 528, divider_x1 + 1203];", source())
        self.assertEqual(layout()["swing_x"], [1236, 1911])

    def test_manifest_defaults_match_the_source(self):
        for name in MANIFESTS:
            for entry in manifest(name).values():
                with self.subTest(manifest=name, parameter=entry["name"]):
                    self.assertIn(entry["type"], ("number", "boolean"))
                    self.assertEqual(scad_value(entry["name"]), entry["default"])

    def test_manifest_defaults_are_in_range(self):
        for name in MANIFESTS:
            for entry in manifest(name).values():
                if entry["type"] == "number":
                    self.assertLessEqual(entry["min"], entry["default"])
                    self.assertLessEqual(entry["default"], entry["max"])
                else:
                    self.assertIsInstance(entry["default"], bool)

    def test_shared_parameters_have_matching_ranges(self):
        assembly = manifest("climbing_assembly")
        for name in MANIFESTS:
            for key, entry in manifest(name).items():
                with self.subTest(manifest=name, parameter=key):
                    self.assertEqual(entry, assembly[key])

    def test_manifest_parameter_sets(self):
        frame = {
            "scale_denominator", "ladder_angle", "frame_depth", "post_size",
            "corner_radius", "beam_depth", "rung_count", "rung_pitch",
            "knee_braces", "climbing_wall", "hold_count", "end_net", "bearer_z",
        }
        net = {
            "scale_denominator", "frame_depth", "post_size", "beam_depth",
            "bearer_z", "net_width", "net_mesh",
        }
        self.assertEqual(set(manifest("climbing_frame")), frame)
        self.assertEqual(set(manifest("climbing_net")), net)
        self.assertEqual(
            set(manifest("climbing_assembly")),
            frame | net | {"slide_run", "show_ground"},
        )
        self.assertEqual(set(manifest("climbing_slide")), {"scale_denominator", "slide_run"})
        self.assertEqual(set(manifest("climbing_swing")), {"scale_denominator", "beam_depth"})
        # the A-frame copies drop only net_width, which their net ignores
        self.assertEqual(manifest("climbing_frame_aframe"), manifest("climbing_frame"))
        cube_net = manifest("climbing_net")
        del cube_net["net_width"]
        self.assertEqual(manifest("climbing_net_aframe"), cube_net)
        cube_assembly = manifest("climbing_assembly")
        del cube_assembly["net_width"]
        self.assertEqual(manifest("climbing_assembly_aframe"), cube_assembly)

    def test_show_ground_is_assembly_only(self):
        for name in ASSEMBLIES:
            self.assertIn("show_ground", manifest(name))
        for name in NON_ASSEMBLY:
            self.assertNotIn("show_ground", manifest(name))

    def test_rung_assert_explains_its_limit(self):
        src = source()
        self.assertIn(
            "assert(monkey_rung_start + (rung_count - 1) * rung_pitch "
            "<= frame_x - post_size - rung_d,",
            src,
        )
        self.assertIn(
            "max_rungs = floor((frame_x - post_size - rung_d - monkey_rung_start) "
            "/ rung_pitch) + 1;",
            src,
        )
        self.assertIn(
            'str("monkey-bar rungs overrun the far side rail: at rung_pitch ", '
            'rung_pitch, " use at most ", max_rungs, " rungs")',
            src,
        )
        entries = manifest("climbing_assembly")
        default_count = entries["rung_count"]["default"]
        default_pitch = entries["rung_pitch"]["default"]
        names = ("rung_count", "rung_pitch", "post_size", "scale_denominator")
        corners = itertools.product(
            *((entries[n]["min"], entries[n]["max"]) for n in names)
        )
        for count, pitch, post, denom in corners:
            rung_d = 1.75 * denom
            lay = layout(post, denom)
            start, frame_x = lay["monkey_rung_start"], lay["frame_x"]
            limit = frame_x - post - rung_d
            max_rungs = math.floor((limit - start) / pitch) + 1
            with self.subTest(count=count, pitch=pitch, post=post, denom=denom):
                passes = start + (count - 1) * pitch <= limit
                self.assertEqual(count <= max_rungs, passes)
                # the defaults fit at every post size and scale
                self.assertLessEqual(start + (default_count - 1) * default_pitch, limit)
                # first rung 150 mm clear of the divider rail
                self.assertEqual(start - rung_d / 2 - lay["divider_x1"], 150)

    def test_default_rungs_clear_the_entrapment_band(self):
        start = layout()["monkey_rung_start"]
        pitch = scad_value("rung_pitch")
        count = int(scad_value("rung_count"))
        denom = scad_value("scale_denominator")
        rungs = [start + i * pitch for i in range(count)]
        self.assertEqual(rungs, [875.5, 1175.5, 1475.5, 1775.5, 2075.5, 2375.5])
        self.assertGreater(pitch - 1.75 * denom, 230)

    def test_default_beam_positions(self):
        self.assertIn("beam_frac = [0.35, 0.65];", source())
        self.assertEqual(layout()["divider_c"], 661)
        frame_y = scad_value("frame_depth")
        self.assertEqual([0.35 * frame_y, 0.65 * frame_y], [700, 1300])

    def test_slide_bay_is_derived_from_the_opening(self):
        src = source()
        self.assertEqual(scad_value("slide_opening"), 520)
        self.assertEqual(scad_value("swing_bay_clear"), 1809)
        for line in (
            "divider_c = post_size / 2 + post_size + slide_opening;",
            "divider_x0 = divider_c - post_size / 2;",
            "divider_x1 = divider_c + post_size / 2;",
            "frame_x = divider_x1 + swing_bay_clear + post_size;",
            "slide_x0 = post_size + (slide_opening - slide_w) / 2;",
            "ladder_x0 = post_size + (slide_opening - ladder_w) / 2;",
            "monkey_rung_start = divider_x1 + 150 + rung_d / 2;",
        ):
            self.assertIn(line, src)
        lay = layout()
        self.assertEqual(
            (lay["divider_c"], lay["divider_x0"], lay["divider_x1"], lay["frame_x"]),
            (661, 614, 708, 2611),
        )
        self.assertEqual((lay["slide_x0"], lay["ladder_x0"]), (104, 104))
        post = scad_value("post_size")
        for x0, w in ((lay["slide_x0"], scad_value("slide_w")), (lay["ladder_x0"], scad_value("ladder_w"))):
            self.assertEqual(x0 - post, lay["divider_x0"] - (x0 + w))
        self.assertGreaterEqual((scad_value("slide_opening") - 506) / 2, 7)

    def test_wall_boards_top_out_flush_with_the_deck(self):
        deck_z = scad_value("deck_z")
        count = math.floor((deck_z - WALL_BASE_Z - WALL_BOARD_W) / WALL_PITCH) + 1
        self.assertEqual(count, WALL_BOARD_COUNT)
        self.assertEqual(WALL_BASE_Z + (count - 1) * WALL_PITCH + WALL_BOARD_W, 1494)
        self.assertEqual(scad_value("wall_board_w") + scad_value("wall_gap"), WALL_PITCH)

    def test_hold_positions_snap_onto_boards(self):
        holds = hold_xy()
        self.assertEqual(
            holds,
            [[400, 350], [1250, 420], [700, 700], [1600, 650], [300, 1000],
             [1000, 1050], [1800, 1000], [600, 1300], [1400, 1350], [900, 450],
             [1700, 1300], [500, 1150]],
        )
        self.assertEqual(
            [hold_z(z) for _, z in holds],
            [350, 447, 747, 650, 1047, 1050, 1047, 1347, 1350, 450, 1347, 1150],
        )
        for _, z in holds:
            centre = hold_z(z)
            i = math.floor((centre - WALL_BASE_Z) / WALL_PITCH)
            board_lo = WALL_BASE_Z + i * WALL_PITCH
            self.assertGreaterEqual(centre - HOLD_H / 2, board_lo)
            self.assertLessEqual(centre + HOLD_H / 2, board_lo + WALL_BOARD_W)
        self.assertEqual(manifest("climbing_frame")["hold_count"]["max"], len(holds))

    def test_default_net_lattice(self):
        frame_y = scad_value("frame_depth")
        net_width = scad_value("net_width")
        mesh = scad_value("net_mesh")
        net_foot = scad_value("bearer_z") + scad_value("post_size")
        beam_z0 = scad_value("frame_h") - scad_value("beam_depth")
        y0 = (frame_y - net_width) / 2
        verticals = scad_range(y0, mesh, y0 + net_width + 1)
        horizontals = scad_range(net_foot, mesh, beam_z0 - 1)
        self.assertEqual(verticals, [250, 550, 850, 1150, 1450, 1750])
        self.assertEqual(horizontals, [244, 544, 844, 1144, 1444, 1744, 2044])

    def test_net_fits_between_the_posts_at_the_default_depth(self):
        self.assertIn(
            "assert(aframe_end || net_width <= frame_y - 2 * post_size,", source()
        )
        entries = manifest("climbing_assembly")
        self.assertLessEqual(
            entries["net_width"]["max"],
            entries["frame_depth"]["default"] - 2 * entries["post_size"]["max"],
        )


def leg_inner_y(z, rake):
    """Mirrors leg_inner_y() in _climbing_frame.scad at the default post_size."""
    post = scad_value("post_size")
    return post / 2 + z * math.tan(rake) + post / (2 * math.cos(rake))


class AFrameEndTests(unittest.TestCase):
    def test_switch_defaults_off_and_is_not_a_parameter(self):
        self.assertIs(scad_value("aframe_end"), False)
        for name in MANIFESTS:
            with self.subTest(manifest=name):
                self.assertNotIn("aframe_end", manifest(name))

    def test_renderables_turn_the_switch_on_after_the_include(self):
        for name in AFRAME_RENDERABLES:
            with self.subTest(renderable=name):
                text = (PROJECT_DIR / f"{name}.scad").read_text(encoding="utf-8")
                include = text.index("include <_climbing_frame.scad>")
                switch = re.search(r"^aframe_end = true;$", text, re.M)
                self.assertIsNotNone(switch)
                self.assertGreater(switch.start(), include)
        for name in ("climbing_frame", "climbing_net", "climbing_assembly",
                     "climbing_slide", "climbing_swing"):
            with self.subTest(renderable=name):
                text = (PROJECT_DIR / f"{name}.scad").read_text(encoding="utf-8")
                self.assertNotIn("aframe_end", text)

    def test_rake_is_derived_from_the_beam_position(self):
        self.assertIn(
            "rake = atan((beam_y[0] - post_size / 2) / beam_z0);", source()
        )
        self.assertIn(
            "function leg_inner_y(z) = post_size / 2 + z * tan(rake) "
            "+ post_size / (2 * cos(rake));",
            source(),
        )
        post = scad_value("post_size")
        beam_z0 = scad_value("frame_h") - scad_value("beam_depth")
        rake = math.atan((0.35 * scad_value("frame_depth") - post / 2) / beam_z0)
        self.assertAlmostEqual(math.degrees(rake), 16.86, places=2)
        self.assertEqual(round(beam_z0 / math.cos(rake)), 2252)
        # a shallower frame gets a steeper A
        for depth, degrees in ((1500, 12.5), (2500, 21.0)):
            r = math.atan((0.35 * depth - post / 2) / beam_z0)
            self.assertAlmostEqual(math.degrees(r), degrees, delta=0.1)

    def test_default_trapezoid_net(self):
        frame_y = scad_value("frame_depth")
        post = scad_value("post_size")
        mesh = scad_value("net_mesh")
        net_foot = scad_value("bearer_z") + post
        beam_z0 = scad_value("frame_h") - scad_value("beam_depth")
        tie_z0 = beam_z0 - post
        rake = math.atan((0.35 * frame_y - post / 2) / beam_z0)
        rows = scad_range(net_foot, mesh, tie_z0 - mesh / 2)
        self.assertEqual(rows, [244, 544, 844, 1144, 1444, 1744])
        widths = [round(frame_y - 2 * leg_inner_y(z, rake)) for z in rows]
        self.assertEqual(widths, [1660, 1478, 1296, 1114, 933, 751])
        # columns straddle the centre and must cross at least two rows
        y_lim = leg_inner_y(net_foot + mesh, rake)
        halves = scad_range(frame_y / 2 + mesh / 2, mesh, frame_y - y_lim)
        columns = sorted(c for y in halves for c in (y, frame_y - y))
        self.assertEqual(columns, [550, 850, 1150, 1450])
        crossings = sum(
            1 for y in columns for z in rows
            if leg_inner_y(z, rake) <= y <= frame_y - leg_inner_y(z, rake)
        )
        self.assertEqual(crossings, 22)
        # tie and bearer span their gap at its widest, their undersides
        self.assertEqual(round(frame_y - 2 * leg_inner_y(tie_z0, rake)), 559)
        self.assertEqual(
            round(frame_y - 2 * leg_inner_y(scad_value("bearer_z"), rake)), 1717
        )

    def test_net_width_assert_is_skipped_in_the_aframe(self):
        # the A-frame manifests have no net_width, so the cube default must
        # not trip the assert at the minimum frame depth
        entries = manifest("climbing_assembly_aframe")
        self.assertNotIn("net_width", entries)
        self.assertGreater(
            scad_value("net_width"),
            entries["frame_depth"]["min"] - 2 * entries["post_size"]["max"],
        )
        self.assertIn("assert(aframe_end || net_width", source())


if __name__ == "__main__":
    unittest.main()
