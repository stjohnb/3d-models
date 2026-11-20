// =====================================
// RF433 bridge carrier PCB enclosure
// Two-part, fully printed box for the assembled RF433 bridge carrier board
// (St-John-Software/electronics, docs/rf433-bridge/PCB.md): a 62 x 60 mm
// 1.6 mm carrier with a DOIT ESP32 DevKit v1 (30-pin, USB-C) and an Ebyte
// E07-M1101D CC1101 module soldered on. Modelled on ha-carlink-enclosure.
// =====================================
// Parts:
//   rf433_enclosure_base -> rf433_enclosure_base.stl
//       Tray: four M3 insert standoffs under the board's holes, a USB window
//       in the -Y wall, an open-topped slot in the +X wall for the SMA jack,
//       and two optional countersunk floor holes for wall/shelf fixing.
//   rf433_enclosure_lid  -> rf433_enclosure_lid.stl
//       Plain plate with a locating lip and four clamp bosses that press the
//       board onto its standoffs (one M3 screw each, into the insert).
//
// Orientation: Z-up. The base prints floor-down as exported. The lid is
// modelled outer-face-down and is turned over onto the base.
//
// Layout frame: model X/Y are centred on the PCB, looking down at the
// component side with X right and Y up. Board-document coordinates (mm from
// the board's top-left corner, X right, Y DOWN) convert with bpos(). The
// cavity is not centred on the board: it grows toward -Y and +X to take the
// devkit's USB-C overhang and the CC1101 module's overhang.
//
// Measured from the assembled board 2026-11-05; see electronics
// docs/rf433-bridge/PCB.md. VERIFY marks values not yet checked on a print.

$fn = 64;

// === Carrier PCB (mm) ===
pcb_l         = 62;
pcb_w         = 60;
pcb_t         = 1.6;
pcb_holes     = [[4, 4], [58, 4], [4, 56], [58, 56]];  // M3 centres, board frame
pcb_keepout_r = 3.5;   // parts-free radius round each hole: standoff/boss d <= 7
pcb_clear     = 0.5;   // board edge to cavity wall, per side
above_pcb     = 16;    // clearance over the board top
below_pcb     = 3;     // clearance under the board
// DOIT ESP32 DevKit v1 (30-pin, USB-C) on 2.54 mm header plastic (board frame);
// its USB end overhangs the carrier's bottom edge
devkit_bx     = [8.55, 36.85];  // design value, not measured
devkit_by     = [8.44, 66.7];   // PCB USB end measured at Y 66.7
usb_face_by   = 68.3;  // USB-C receptacle face (measured)
devkit_top    = 7.3;   // devkit height above the board top (design value)
antenna_bx    = [8, 37.5];    // ANTENNA_KEEPOUT: no metal here
antenna_by    = [0, 16.5];
usb_bx        = 22.7;  // USB-C centre (board X, measured)
usb_span      = 14;    // window width along X (confirmed by the 0.1.0 print)
usb_z0        = 2;     // window bottom above the board top (confirmed by the 0.1.0 print)
usb_h         = 10;    // window height (confirmed by the 0.1.0 print)
usb_gap       = 0.5;   // USB-C face to -Y inner wall
// Ebyte E07-M1101D, PCB and SMA end overhanging the right edge
mod_bx        = [38.5, 67.9];   // PCB end measured at X 67.9
mod_by        = [35.6, 50.6];   // top edge measured; bottom = top + 15 mm width
mod_clear     = 1.0;   // module PCB end to +X inner wall
mod_top       = 3.5;   // module body height above the board top (VERIFY)
sma_tip_bx    = 69.4;  // SMA jack outer end (measured)
sma_by        = 42.81; // SMA axis (board Y, measured 42.8)
sma_z         = 3;     // SMA axis above the board top (measured)
sma_slot_w    = 11;    // slot width for the antenna nut (VERIFY)

// === Enclosure ===
wall       = 2.4;
floor_t    = 3;
corner_r   = 3;
standoff_h = 5;
standoff_d = 7;        // == 2 * pcb_keepout_r
lid_t      = 2.4;
lip_t      = 1.6;
lip_d      = 4;
lip_clear  = 0.3;
boss_extra = 0;

// === Fixings: M3 heat-set insert in each standoff, one screw per corner ===
insert_hole_d  = 4.0;
insert_depth   = 6;
insert_chamfer = 0.5;
screw_l        = 25;   // M3 x 25 countersunk (VERIFY length once printed)
screw_clear    = 3.4;
screw_head     = 6.8;

// === Optional wall/shelf fixing: countersunk holes through the floor ===
floor_fixings = true;
fixing_d      = 4.2;
fixing_head_d = 8.5;
fixing_cs_h   = 2;
fixing_bx     = 48;
fixing_by     = [20, 56];

// === Derived ===
function bpos(p) = [p[0] - pcb_l/2, pcb_w/2 - p[1]];   // board frame -> model
function mid(r) = (r[0] + r[1]) / 2;
pcb_top    = floor_t + standoff_h + pcb_t;
inner_d    = standoff_h + pcb_t + above_pcb;
// Cavity extent in the board frame: the board edge plus pcb_clear, grown to
// take the devkit's USB-C overhang (-Y) and the CC1101 overhang (+X).
cav_bx     = [-pcb_clear, max(pcb_l + pcb_clear, mod_bx[1] + mod_clear)];
cav_by     = [-pcb_clear, max(pcb_w + pcb_clear, usb_face_by + usb_gap)];
inner_l    = cav_bx[1] - cav_bx[0];
inner_w    = cav_by[1] - cav_by[0];
cav_c      = bpos([mid(cav_bx), mid(cav_by)]);   // cavity centre, model frame
outer_l    = inner_l + 2 * wall;
outer_w    = inner_w + 2 * wall;
inner_r    = max(0.5, corner_r - wall);
base_h     = floor_t + inner_d;
boss_h     = above_pcb + boss_extra;
usb_cx     = bpos([usb_bx, 0])[0];
sma_cy     = bpos([0, sma_by])[1];
sma_cz     = pcb_top + sma_z;
nut_top    = sma_z + sma_slot_w/2;
cs_h       = (screw_head - screw_clear)/2;

// distance from point p to the rectangle bx x by (board frame)
function rect_dist(p, bx, by) =
    norm([max(bx[0] - p[0], 0, p[0] - bx[1]), max(by[0] - p[1], 0, p[1] - by[1])]);

assert(standoff_h >= below_pcb, "standoff_h must give below_pcb under the board");
assert(standoff_d <= 2 * pcb_keepout_r, "standoffs intrude on the 3.5 mm hole keep-out");
assert(inner_r <= pcb_clear * sqrt(2) / (sqrt(2) - 1),
       "inner corner radius clips the PCB corners: lower corner_r or raise wall");
assert(insert_hole_d <= standoff_d - 2.5, "insert pocket leaves too thin a standoff wall");
assert(insert_depth <= standoff_h + floor_t - 1.5, "insert pocket breaks through the floor");
assert(screw_l >= lid_t + boss_h + pcb_t + 4 && screw_l <= lid_t + boss_h + pcb_t + insert_depth,
       "screw_l must reach 4 mm into the insert without bottoming out");
assert(cs_h < lid_t, "lid too thin for the countersink");
assert(usb_z0 + usb_h <= above_pcb - lip_d, "USB window runs into the lid lip");
assert(above_pcb - lip_d > max(devkit_top, nut_top, mod_top) + 1,
       "lid lip comes within 1 mm of the devkit, module or antenna nut: raise above_pcb or lower lip_d");
assert(sma_cy - sma_slot_w/2 > cav_c[1] - inner_w/2 + standoff_d/2 + 1
       && sma_cy + sma_slot_w/2 < cav_c[1] + inner_w/2 - standoff_d/2 - 1,
       "SMA slot runs into a corner");
assert(sma_cz - sma_slot_w/2 > floor_t + 1, "SMA slot breaks through the floor");
assert(fixing_cs_h < floor_t - 0.8, "floor fixing countersink leaves too thin a floor");
// The measured devkit and module outlines sit inside the cavity, clear of the walls.
for (part = [[devkit_bx, devkit_by], [mod_bx, mod_by]])
    assert(part[0][0] - cav_bx[0] >= 0.5 && cav_bx[1] - part[0][1] >= 0.5
           && part[1][0] - cav_by[0] >= 0.5 && cav_by[1] - part[1][1] >= 0.5,
           "devkit or CC1101 module comes within 0.5 mm of a wall");
assert(usb_face_by + usb_gap <= cav_by[1], "USB-C face presses on the -Y wall");
assert(sma_tip_bx >= cav_bx[1], "SMA jack does not reach the +X wall slot");
// Standoff and lid-boss circles clear the devkit and the module.
for (h = pcb_holes) {
    assert(rect_dist(h, devkit_bx, devkit_by) - standoff_d/2 >= 0.5,
           "a standoff or lid boss comes within 0.5 mm of the devkit");
    assert(rect_dist(h, mod_bx, mod_by) - standoff_d/2 >= 0.5,
           "a standoff or lid boss comes within 0.5 mm of the CC1101 module");
}
// No metal over the antenna end: every insert/screw position stays outside
// the keep-out rectangle by more than the standoff radius.
for (p = pcb_holes)
    assert(p[0] + standoff_d/2 < antenna_bx[0] || p[0] - standoff_d/2 > antenna_bx[1]
           || p[1] + standoff_d/2 < antenna_by[0] || p[1] - standoff_d/2 > antenna_by[1],
           "a fixing sits in the antenna keep-out");
// Floor fixings clear the keep-out, devkit, module, floor outline and standoffs.
if (floor_fixings)
    for (y = fixing_by) {
        p = [fixing_bx, y];
        r = fixing_head_d/2;
        assert(rect_dist(p, antenna_bx, antenna_by) > r, "floor fixing under the antenna keep-out");
        assert(rect_dist(p, devkit_bx, devkit_by) > r, "floor fixing under the devkit");
        assert(rect_dist(p, mod_bx, mod_by) > r, "floor fixing under the CC1101 module");
        assert(p[0] - r > cav_bx[0] && p[0] + r < cav_bx[1]
               && p[1] - r > cav_by[0] && p[1] + r < cav_by[1],
               "floor fixing head runs off the floor");
        for (h = pcb_holes)
            assert(norm(p - h) > r + standoff_d/2, "floor fixing head overlaps a standoff");
    }

// === Modules ===

module rbox(l, w, h, r) {
    hull()
        for (sx = [-1, 1], sy = [-1, 1])
            translate([sx * (l/2 - r), sy * (w/2 - r), 0])
                cylinder(r = r, h = h);
}

module insert_hole(depth) {
    translate([0, 0, -depth]) cylinder(d = insert_hole_d, h = depth + 0.01);
    translate([0, 0, -insert_chamfer])
        cylinder(d1 = insert_hole_d, d2 = insert_hole_d + 2 * insert_chamfer,
                 h = insert_chamfer + 0.01);
}

module hole_positions() {
    for (p = pcb_holes) translate(bpos(p)) children();
}

// Open-topped slot through the +X wall for the SMA jack and antenna nut.
module sma_slot() {
    translate([cav_c[0] + inner_l/2 - 1, sma_cy, sma_cz]) rotate([0, 90, 0]) hull() {
        cylinder(d = sma_slot_w, h = wall + 2);
        translate([-(inner_d + 2), -sma_slot_w/2, 0]) cube([inner_d + 2, sma_slot_w, wall + 2]);
    }
}

// Base tray: floor at z=0, opening toward +Z.
module rf433_enclosure_base() {
    difference() {
        union() {
            difference() {
                translate(cav_c) rbox(outer_l, outer_w, base_h, corner_r);
                translate([cav_c[0], cav_c[1], floor_t])
                    rbox(inner_l, inner_w, inner_d + 1, inner_r);
            }
            hole_positions()
                translate([0, 0, floor_t - 0.01])
                    cylinder(d = standoff_d, h = standoff_h + 0.01);
        }
        hole_positions()
            translate([0, 0, floor_t + standoff_h]) insert_hole(insert_depth);
        // USB window through the -Y wall
        translate([usb_cx - usb_span/2, cav_c[1] - inner_w/2 - wall - 1, pcb_top + usb_z0])
            cube([usb_span, wall + 2, usb_h]);
        sma_slot();
        if (floor_fixings)
            for (y = fixing_by) translate(bpos([fixing_bx, y])) {
                translate([0, 0, -1]) cylinder(d = fixing_d, h = floor_t + 2);
                translate([0, 0, floor_t - fixing_cs_h])
                    cylinder(d1 = fixing_d, d2 = fixing_head_d, h = fixing_cs_h + 0.01);
            }
    }
}

// Lid in the layout frame: outer face at z=0, features rising toward +Z.
module lid_frame() {
    difference() {
        union() {
            translate(cav_c) rbox(outer_l, outer_w, lid_t, corner_r);
            translate([cav_c[0], cav_c[1], lid_t - 0.01])
                difference() {
                    rbox(inner_l - 2 * lip_clear, inner_w - 2 * lip_clear,
                         lip_d + 0.01, max(0.5, inner_r - lip_clear));
                    translate([0, 0, -1])
                        rbox(inner_l - 2 * (lip_clear + lip_t),
                             inner_w - 2 * (lip_clear + lip_t), lip_d + 3,
                             max(0.5, inner_r - lip_clear - lip_t));
                }
            hole_positions()
                translate([0, 0, lid_t - 0.01])
                    cylinder(d = standoff_d, h = boss_h + 0.01);
        }
        hole_positions() {
            translate([0, 0, -1]) cylinder(d = screw_clear, h = lid_t + boss_h + 2);
            translate([0, 0, -0.01]) cylinder(d1 = screw_head, d2 = screw_clear, h = cs_h);
        }
    }
}

// Lid in print orientation (turned over about X, which mirrors Y).
module rf433_enclosure_lid() {
    mirror([0, 1, 0]) lid_frame();
}
