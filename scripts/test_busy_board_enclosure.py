"""Pins the busy-board-enclosure customizer manifests and library against
the busy board's docs/busy-board/PCB.md (v2.0) and docs/busy-board-v3/PCB.md
(v3.0) (St-John-Software/electronics).

Run with: python3 -m unittest test_busy_board_enclosure
"""

import json
import math
import pathlib
import re
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PROJECT_DIR = REPO_ROOT / "busy-board-enclosure"
LIBRARY = PROJECT_DIR / "_busy_board_enclosure.scad"
PLATE_SCAD = PROJECT_DIR / "busy_board_plate.scad"
FRAME = PROJECT_DIR / "busy_board_frame.parameters.json"
PLATE = PROJECT_DIR / "busy_board_plate.parameters.json"
TRAY = PROJECT_DIR / "busy_board_tray.parameters.json"
DOOR = PROJECT_DIR / "busy_board_battery_door.parameters.json"
MANIFESTS = (FRAME, PLATE, TRAY, DOOR)
# Parameters that size more than one part, and the manifests that must expose them.
SHARED_PARAMS = {
    ("wall", "corner_r", "edge_r", "inner_d", "insert_hole_d", "lip_clear"): (FRAME, TRAY),
    ("floor_t", "batt_l", "batt_w", "door_t", "door_clear"): (TRAY, DOOR),
    ("panel_t",): (FRAME, PLATE),
    ("board_v3",): (FRAME, PLATE, TRAY),
}
BOARDS = ("v2", "v3")
# Fit parameters, each exposed on the one part it sizes.
PART_PARAMS = {
    FRAME: ("frame_lip_t", "frame_overlap", "lip_r", "lip_d"),
    PLATE: ("tgl_hole_d", "tgl_lug", "tgl_lug_r", "tgl_lug_d", "pot_lug_d",
            "slide_screw_pitch", "slide_screw_d", "grille_hole_d"),
    TRAY: ("batt_h", "chg_l", "chg_w", "chg_seat", "usb_pocket_d",
           "pcm_l", "pcm_w"),
}


def source():
    return LIBRARY.read_text(encoding="utf-8")


def scad_value(name):
    match = re.search(rf"^{name}\s*=\s*([^;]+);", source(), re.M)
    if match is None:
        raise AssertionError(f"{name} not found in {LIBRARY.name}")
    return match.group(1).strip()


def scad_number(name):
    return float(scad_value(name))


def scad_points(name):
    # OpenSCAD vector syntax, not JSON: pull every [x, y] pair.
    pairs = re.findall(r"\[\s*([\d.]+)\s*,\s*([\d.]+)\s*\]", scad_value(name))
    return [(float(x), float(y)) for x, y in pairs]


def manifest_names(path):
    return {e["name"] for e in json.loads(path.read_text(encoding="utf-8"))["parameters"]}


class BusyBoardEnclosureManifestTests(unittest.TestCase):
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

    def test_shared_parameters_are_exposed_together(self):
        for names, manifests in SHARED_PARAMS.items():
            for name in names:
                for path in manifests:
                    with self.subTest(name=name, manifest=path.name):
                        self.assertIn(name, manifest_names(path))

    def test_part_parameters_are_exposed(self):
        for path, names in PART_PARAMS.items():
            for name in names:
                with self.subTest(name=name, manifest=path.name):
                    self.assertIn(name, manifest_names(path))

    def test_shared_parameters_agree(self):
        entries = {}
        for path in MANIFESTS:
            for entry in json.loads(path.read_text(encoding="utf-8"))["parameters"]:
                entries.setdefault(entry["name"], []).append(entry)
        for name, found in entries.items():
            with self.subTest(name=name):
                self.assertEqual(len({(e.get("min"), e.get("max"), e["default"]) for e in found}), 1)


class BusyBoardEnclosureRequirementTests(unittest.TestCase):
    """Pins the board v2.0 and v3.0 figures from each PCB.md "Mechanical and enclosure"."""

    def test_board_selection(self):
        self.assertEqual(scad_value("board_v3"), "true")
        for name in ("pcb_l", "pcb_holes", "ds1_c", "bar_x", "ring_c", "enc_bc", "btn_bc",
                     "btn_led_c", "pot_bc", "tgl_bc", "tgl_led_c", "slide_bc",
                     "slide_led_c", "buzzer_bc"):
            with self.subTest(name=name):
                self.assertEqual(scad_value(name), f"board_v3 ? v3_{name} : v2_{name}")

    def test_board_outline(self):
        self.assertEqual(scad_number("v2_pcb_l"), 222)
        self.assertEqual(scad_number("v3_pcb_l"), 210)
        self.assertEqual(scad_number("pcb_w"), 222)
        self.assertEqual(scad_number("pcb_t"), 1.6)

    def test_mounting_holes(self):
        for board, mid, right in (("v2", 111, 217), ("v3", 105, 205)):
            with self.subTest(board=board):
                self.assertEqual(
                    sorted(scad_points(f"{board}_pcb_holes")),
                    sorted([(5, 5), (mid, 5), (right, 5), (5, 111), (right, 111),
                            (5, 217), (mid, 217), (right, 217)]),
                )
        self.assertEqual(scad_number("pcb_keepout_r"), 3.5)
        self.assertLessEqual(scad_number("boss_d"), 7)

    def test_displays(self):
        self.assertEqual(scad_points("v2_ds1_c"), [(111, 36)])
        self.assertEqual(scad_points("v3_ds1_c"), [(105, 36)])
        self.assertEqual(scad_points("ds1_body"), [(50.4, 19.0)])

    def test_bar_graphs(self):
        self.assertEqual(scad_value("v2_bar_x"), "[73, 111, 149]")
        self.assertEqual(scad_value("v3_bar_x"), "[67, 105, 143]")
        self.assertEqual(scad_points("bar_y"), [(62, 116)])   # LED 10, LED 1
        self.assertEqual(scad_number("bar_led"), 5.0)

    def test_ring_leds(self):
        side_y = (30, 60, 98, 132, 168, 196)
        for board, top_x, right in (
                ("v2", (17, 44, 71, 98, 124, 151, 178, 205), 214),
                ("v3", (17, 42, 67, 92, 118, 143, 168, 193), 202)):
            expected = (
                [(x, 8) for x in top_x]                    # D1-D8
                + [(right, y) for y in side_y]             # D9-D14
                + [(x, 214) for x in reversed(top_x)]      # D15-D22
                + [(8, y) for y in reversed(side_y)]       # D23-D28
            )
            with self.subTest(board=board):
                self.assertEqual(scad_points(f"{board}_ring_c"), expected)

    def test_encoder_ring(self):
        self.assertEqual(scad_points("v2_enc_bc"), [(40, 44)])
        self.assertEqual(scad_points("v3_enc_bc"), [(34, 44)])
        self.assertEqual(scad_number("enc_ring_r"), 15.5)
        self.assertEqual(scad_number("enc_ring_n"), 12)

    def test_control_lights(self):
        self.assertEqual(
            scad_points("v2_btn_led_c"),
            [(x, 160) for x in (35, 73, 111, 149, 187)] + [(182, 74)],   # D71-D76
        )
        self.assertEqual(scad_points("v2_tgl_led_c"), [(54, 88), (54, 122), (168, 88)])
        self.assertEqual(scad_points("v2_slide_led_c"), [(168, 122)])
        self.assertEqual(
            scad_points("v3_btn_led_c"),
            [(x, 160) for x in (48, 86, 124, 162)] + [(176, 74)],   # D71-D74, D76
        )
        self.assertEqual(scad_points("v3_tgl_led_c"), [(48, 88), (48, 122), (162, 88)])
        self.assertEqual(scad_points("v3_slide_led_c"), [(162, 122)])

    def test_cut_outs(self):
        self.assertEqual(
            scad_points("v2_btn_bc"),
            [(x, 184) for x in (35, 73, 111, 149, 187)] + [(182, 44)],   # BTN1-5, PWR
        )
        self.assertEqual(scad_points("v2_pot_bc"), [(73, 140), (111, 140), (149, 140)])
        self.assertEqual(scad_points("v2_tgl_bc"), [(34, 88), (34, 122), (188, 88)])
        self.assertEqual(scad_points("v2_slide_bc"), [(188, 122)])
        self.assertEqual(
            scad_points("v3_btn_bc"),
            [(x, 184) for x in (48, 86, 124, 162)] + [(176, 44)],   # BTN1-4, PWR
        )
        self.assertEqual(scad_points("v3_pot_bc"), [(67, 140), (105, 140), (143, 140)])
        self.assertEqual(scad_points("v3_tgl_bc"), [(28, 88), (28, 122), (182, 88)])
        self.assertEqual(scad_points("v3_slide_bc"), [(182, 122)])
        self.assertEqual(scad_points("slide_cut"), [(22, 12)])
        self.assertEqual(scad_number("enc_cut_d"), 16)
        self.assertEqual(scad_number("btn_cut_d"), 32)
        self.assertEqual(scad_number("tgl_cut_d"), 17)
        self.assertEqual(scad_number("pot_cut_d"), 20)

    def test_button_counts_follow_the_board(self):
        text = source()
        self.assertIn("len(btn_bc) == (board_v3 ? 5 : 6)", text)
        self.assertIn("len(led_c) == (board_v3 ? 49 : 50)", text)
        self.assertEqual(len(scad_points("v2_btn_bc")), 6)
        self.assertEqual(len(scad_points("v3_btn_bc")), 5)

    def test_chosen_parts(self):
        # Switch Electronics parts: APEM 5636A (1/4-40 bushing), 124002 slide
        # switch, CLIFF K15 knob, RK163 pot (M7 x 0.75, 7 mm cut-out).
        self.assertEqual(scad_number("tgl_hole_d"), 6.6)
        self.assertEqual(scad_number("slide_screw_pitch"), 19)
        self.assertEqual(scad_number("knob_d"), 20)
        self.assertEqual(scad_number("pot_hole_d"), 7.4)
        self.assertLessEqual(scad_number("tgl_body_d"), scad_number("tgl_cut_d"))

    def test_buzzer_and_grille(self):
        self.assertEqual(scad_points("v2_buzzer_bc"), [(184, 146)])
        self.assertEqual(scad_points("v3_buzzer_bc"), [(178, 146)])
        self.assertEqual(scad_number("buzzer_d"), 12)
        # Child-safety rule 8: grille holes at most 2 mm across.
        self.assertLessEqual(scad_number("grille_hole_d"), 2)

    def test_connector_and_part_heights(self):
        self.assertEqual(scad_number("jst_h"), 10)
        self.assertEqual(scad_number("jst_lead_h"), 15)
        self.assertEqual(scad_number("f1_h"), 12)
        self.assertEqual(scad_number("u1_h"), 9)
        self.assertEqual(scad_number("u2_h"), 11)
        self.assertEqual(scad_number("buzzer_h"), 9.5)
        self.assertEqual(scad_number("below_pcb"), 3)
        pcb_to_panel = scad_number("pcb_to_panel")
        self.assertGreaterEqual(pcb_to_panel, scad_number("jst_h") + 2)
        self.assertGreaterEqual(pcb_to_panel, scad_number("jst_lead_h"))

    def test_leds_clear_the_plate(self):
        # No spacers: the LEDs sit on the board, behind the clear plate.
        self.assertEqual(scad_number("led_raise"), 0)
        tip = scad_number("led_h") + scad_number("led_raise")
        self.assertLessEqual(tip, scad_number("pcb_to_panel") - 1)
        self.assertEqual(scad_number("standoff_l"), scad_number("pcb_to_panel"))

    def test_v3_part_heights(self):
        # docs/busy-board-v3/PCB.md "Mechanical and enclosure": all LEDs
        # 5050, on-board boost, 1812 F1.
        self.assertEqual(scad_number("v3_led_span"), 7.1)
        self.assertEqual(scad_number("v3_led_h"), 1.6)
        self.assertEqual(scad_number("v3_boost_h"), 3)
        self.assertEqual(scad_number("v3_f1_h"), 2)
        self.assertEqual(scad_number("v3_buzzer_h"), 7.5)
        tallest = max(scad_number(n) for n in (
            "u1_h", "v3_boost_h", "v3_f1_h", "j9_h", "jst_h", "ds1_h", "v3_buzzer_h"))
        self.assertGreaterEqual(scad_number("pcb_to_panel"), tallest + 1)
        self.assertIn("pcb_to_panel >= max(u1_h, v3_boost_h, v3_f1_h, j9_h, jst_h, ds1_h, "
                      "v3_buzzer_h) + 1", source())

    def test_v3_leds_clear_the_plate(self):
        tip = scad_number("v3_led_h") + scad_number("led_raise")
        self.assertLessEqual(tip, scad_number("pcb_to_panel") - 1)
        # 5050 tops sit 13.4 mm behind the plate (v2's 5 mm LEDs: 6.4 mm).
        self.assertAlmostEqual(scad_number("pcb_to_panel") - tip, 13.4)
        self.assertAlmostEqual(
            scad_number("pcb_to_panel") - scad_number("led_h") - scad_number("led_raise"), 6.4)
        self.assertIn("v3_led_tip <= pcb_to_panel - 1", source())

    def test_outer_size_fits_the_bed(self):
        per_side = sum(scad_number(n) for n in ("pcb_clear", "post_gap", "lip_clear"))
        per_side += 2 * scad_number("post_r") + scad_number("wall")
        # v3: 235.6 along X by 247.6 along Y; v2: 247.6 square.
        self.assertAlmostEqual(scad_number("v3_pcb_l") + 2 * per_side, 235.6)
        self.assertAlmostEqual(scad_number("v2_pcb_l") + 2 * per_side, 247.6)
        self.assertAlmostEqual(scad_number("pcb_w") + 2 * per_side, 247.6)
        self.assertLessEqual(scad_number("pcb_w") + 2 * per_side, 250)


class BusyBoardClearFrontTests(unittest.TestCase):
    """Pins the clear polycarbonate front and its black frame."""

    def test_plate_is_three_mm(self):
        self.assertEqual(scad_number("panel_t"), 3)
        self.assertEqual(scad_number("plate_r"), 3)

    def test_plate_size(self):
        per_side = (scad_number("pcb_clear") + scad_number("post_gap")
                    - scad_number("plate_clear"))
        # v3: 213.4 along X by 225.4 along Y; v2: 225.4 square.
        self.assertAlmostEqual(scad_number("v3_pcb_l") + 2 * per_side, 213.4)
        self.assertAlmostEqual(scad_number("v2_pcb_l") + 2 * per_side, 225.4)
        self.assertAlmostEqual(scad_number("pcb_w") + 2 * per_side, 225.4)
        self.assertIn("frame_window([frame_win_l, frame_win_w], frame_win_r, frame_t)", source())
        self.assertEqual(source().count("[frame_win_l, frame_win_w], frame_win_r"), 4)

    def test_frame_lip_covers_the_cut_edge(self):
        self.assertGreaterEqual(scad_number("frame_overlap"), 3)
        self.assertLessEqual(scad_number("lip_r"), scad_number("frame_lip_t") - 0.8)

    def test_no_led_holes_or_windows(self):
        # Child-safety rules 1 and 8: the plate has no LED holes and no
        # display windows; the board is seen through it.
        text = source()
        for name in ("led_hole_d", "chamfered_window", "window_clear",
                     "lug_slot", "slide_insert_d", "busy_board_panel"):
            with self.subTest(name=name):
                self.assertIsNone(re.search(rf"\b{name}\b", text))
        self.assertIsNone(re.search(r"(?m)^windows\s*=", text))

    def test_plate_renderable_exports_the_dxf(self):
        text = PLATE_SCAD.read_text(encoding="utf-8")
        self.assertRegex(text, r"(?m)^export_dxf *= *false;")
        self.assertIn("plate_profile()", text)

    def test_encoder_has_no_tab_hole_by_default(self):
        self.assertEqual(scad_value("enc_lug"), "false")


class BusyBoardSlideStackTests(unittest.TestCase):
    """Mirrors the slide-stack and LED-standoff asserts so bad values are known to fail."""

    def failures(self, board="v3", **over):
        def num(name):
            return over[name] if name in over else scad_number(name)

        slot_x = float(re.match(r"\[\s*([\d.]+)", scad_value("slide_slot")).group(1))
        bc = scad_points(f"{board}_slide_bc")[0]
        enc = scad_points(f"{board}_enc_bc")[0]
        ring_r = scad_number("enc_ring_r")
        leds = (scad_points(f"{board}_ring_c") + scad_points(f"{board}_btn_led_c")
                + scad_points(f"{board}_tgl_led_c") + scad_points(f"{board}_slide_led_c"))
        for i in range(12):
            a = math.radians(i * 30)
            leds.append((enc[0] + ring_r * math.sin(a), enc[1] - ring_r * math.cos(a)))
        pitch = num("slide_screw_pitch")
        pts = [(bc[0] + sx * pitch / 2, bc[1]) for sx in (-1, 1)]
        failed = set()
        # A standoff meets an LED on the board: the wider of v2's flange and v3's 5050.
        need = num("boss_d") / 2 + max(num("led_flange_d"), num("v3_led_span")) / 2 + 1
        if any(math.dist(c, h) < need for c in leds for h in scad_points(f"{board}_pcb_holes")):
            failed.add("led_standoff")
        # The slide nuts sit 13 mm above a v3 5050, so only v2's flange bounds them.
        need = num("slide_nut_d") / 2 + num("led_flange_d") / 2 + 0.5
        if any(math.dist(p, c) < need for p in pts for c in leds):
            failed.add("nut_led")
        if num("slide_screw_l") - num("panel_t") > num("pcb_to_panel") - 1:
            failed.add("screw_board")
        if pitch / 2 < slot_x / 2 + 2 + num("slide_head_d") / 2 + 1:
            failed.add("head_slot")
        return failed

    def test_defaults_pass(self):
        for board in BOARDS:
            with self.subTest(board=board):
                self.assertEqual(self.failures(board), set())
                bc = scad_points(f"{board}_slide_bc")[0]
                d80 = scad_points(f"{board}_slide_led_c")[0]
                self.assertAlmostEqual(
                    bc[0] - d80[0] - scad_number("slide_screw_pitch") / 2, 10.5)

    def test_nut_on_led_fails(self):
        for board in BOARDS:
            with self.subTest(board=board):
                self.assertEqual(self.failures(board, slide_screw_pitch=36), {"nut_led"})

    def test_screw_into_board_fails(self):
        for board in BOARDS:
            with self.subTest(board=board):
                self.assertEqual(self.failures(board, slide_screw_l=20), {"screw_board"})

    def test_wide_led_fails_standoff_not_nut(self):
        for board in BOARDS:
            with self.subTest(board=board):
                self.assertEqual(self.failures(board, v3_led_span=20), {"led_standoff"})
                self.assertEqual(self.failures(board, led_flange_d=20),
                                 {"led_standoff", "nut_led"})

    def test_small_pitch_fails_head_slot(self):
        for board in BOARDS:
            with self.subTest(board=board):
                self.assertEqual(self.failures(board, slide_screw_pitch=18), {"head_slot"})

    def test_manifest_pitch_range_passes(self):
        entry = next(e for e in json.loads(PLATE.read_text(encoding="utf-8"))["parameters"]
                     if e["name"] == "slide_screw_pitch")
        for board in BOARDS:
            for key in ("min", "max"):
                with self.subTest(board=board, bound=key):
                    self.assertEqual(self.failures(board, slide_screw_pitch=entry[key]), set())

    def test_stack_asserts_in_library(self):
        text = source()
        self.assertRegex(
            text, r"norm\(p - bpos\(c\)\) >= slide_nut_d/2 \+ led_flange_d/2 \+ 0\.5")
        self.assertIn("a slide-switch nut or screw hits an LED", text)
        self.assertIn("slide_screw_l - panel_t <= pcb_to_panel - 1", text)
        self.assertIn("slide-switch screws reach the board", text)
        self.assertIn("norm(c - h) >= boss_d/2 + max(led_flange_d, v3_led_span)/2 + 1", text)
        self.assertIn("an LED runs into a PCB standoff", text)

    def test_heads_in_face(self):
        block = re.search(r"^face\s*=\s*concat\((.*?)\);", source(), re.M | re.S).group(1)
        self.assertIn("[for (p = slide_screw_pts) [p, slide_head_d/2]]", block)
        self.assertEqual(scad_number("slide_nut_d"), 4.6)
        self.assertEqual(scad_number("slide_screw_l"), 10)
        self.assertEqual(scad_number("slide_head_d"), 3.8)


if __name__ == "__main__":
    unittest.main()
