// _muesli_dispenser.scad — shared parameters and modules for the rotary muesli
// dispenser that bolts through the side wall of a ~200 x 300 x 200 mm clip-lid
// cereal box.
//
// Coordinate frame (native OpenSCAD Z-up — never add a top-level
// rotate([-90,0,0]); the viewers apply Z-up -> Y-up themselves):
//   * The box's outer wall face is the plane Y = 0. Box interior is Y < 0.
//     +Y points away from the box, out over the bowl.
//   * The drum axis is the X axis at (Y = bore_y, Z = 0), i.e. it runs
//     HORIZONTALLY AND PARALLEL TO THE WALL. The knob comes out of the +X end.
//   * Muesli path: box interior -> port through the wall at Z = port_z ->
//     funnel throat sloping down and out -> drum bore -> half turn ->
//     chute -> bowl.

$fn = 64;

// --- Box / mounting -------------------------------------------------------
wall_t        = 2.0;   // box wall thickness at the mounting patch
port_d        = 42;    // hole-saw port through the box wall
floor_offset  = 20;    // port bottom edge above the box's internal floor
screw_d       = 4.5;   // M4 clearance
nut_af        = 7.0;   // M4 nut across-flats
nut_h         = 3.4;   // M4 nut thickness

// --- Drum -----------------------------------------------------------------
drum_d        = 56;
drum_clear    = 0.5;
bore_d        = drum_d + drum_clear;
drum_len      = 64;
pocket_len    = 52;    // axial length of the scoop pocket
pocket_depth  = 32;    // radial cut depth measured down from the drum top
journal_d     = 13;
journal_len   = 6;
shaft_af      = 10;    // hex drive shaft across-flats
shaft_len     = 16;
knob_pilot_d  = 3.4;   // M4 self-tapping pilot down the shaft axis
knob_pilot_h  = 14;

// --- Housing --------------------------------------------------------------
wall_min      = 3.2;
flange_t      = 5;
end_wall_t    = 8;
cap_t         = 5;
chamber_len   = drum_len + 0.6;
x_open        = chamber_len / 2;
x_back        = chamber_len / 2 + end_wall_t;
bore_y        = flange_t + bore_d / 2 + 1.5;
throat_gap    = 4;
port_z        = bore_d / 2 + throat_gap + port_d / 2;
chute_top_in  = 8;                          // chute mouth starts this far up
                                            // from the bottom of the bore
chute_top_z   = -bore_d / 2 + chute_top_in;
chute_top_w   = 2 * sqrt(pow(bore_d / 2, 2) - pow(chute_top_z, 2));
chute_out     = 22;    // +Y offset of the chute mouth from the bore axis
chute_bot     = -44;   // Z of the chute mouth
chute_mouth_d = 32;    // Y depth of the chute mouth
cap_boss_d    = 12;
cap_boss_dz   = 42;
cap_boss_y    = 28;
boss_len      = 14;
trap_x        = 8;

// --- Flange / ring --------------------------------------------------------
flange_w      = 110;
flange_top    = port_z + port_d / 2 + 14;
flange_bot    = -14;
flange_r      = 8;
bolt_dx       = 47;
bolt_dz       = 20;
ring_w        = 110;
ring_h        = 60;
ring_t        = 6;

// --- Knob -----------------------------------------------------------------
knob_d        = 46;
knob_h        = 18;
knob_flutes   = 8;

// --- Drill template -------------------------------------------------------
template_t    = 3;

eps           = 0.01;

// --- Guards ---------------------------------------------------------------
assert(port_z - port_d / 2 >= bore_d / 2 + 3, "port must clear the drum bore");
assert(drum_d - pocket_depth >= 8, "pocket must leave a solid drum floor");
assert(drum_len - pocket_len >= 8, "drum needs sealing end discs");
assert(drum_clear >= 0.3 && drum_clear <= 0.8, "drum clearance out of range");
assert(bolt_dx >= x_back + screw_d / 2 + 2, "wall screws must clear the housing");
assert(journal_d + 0.6 >= shaft_af / cos(30) + 0.4, "cap bore must pass the hex shaft");
assert(bore_y - bore_d / 2 >= flange_t, "bore must not break the flange face");

// --- Primitives -----------------------------------------------------------

// Rounded rectangular plate occupying Y in [0, thick].
module rounded_plate(w, h, z_mid, thick, r) {
    hull()
        for (sx = [-1, 1]) for (sz = [-1, 1])
            translate([sx * (w / 2 - r), 0, z_mid + sz * (h / 2 - r)])
                rotate([-90, 0, 0]) cylinder(r = r, h = thick);
}

// Cylinder on the drum axis, from X = x0 to X = x1.
module bore_cyl(extra, x0, x1) {
    translate([x0, bore_y, 0]) rotate([0, 90, 0])
        cylinder(d = bore_d + 2 * extra, h = x1 - x0);
}

module flange_plate() {
    rounded_plate(flange_w, flange_top - flange_bot,
                  (flange_top + flange_bot) / 2, flange_t, flange_r);
}

module housing_solid() {
    hull() {
        bore_cyl(wall_min, -x_back, x_open);
        translate([-x_back, 0, -(bore_d / 2 + wall_min)])
            cube([x_back + x_open, flange_t, bore_d + 2 * wall_min]);
    }
}

module throat_solid() {
    hull() {
        bore_cyl(wall_min, -x_back, x_open);
        translate([0, flange_t / 2, port_z])
            cube([pocket_len + 2 * wall_min, flange_t, port_d + 2 * wall_min],
                 center = true);
    }
}

module chute_solid() {
    hull() {
        translate([0, bore_y, chute_top_z])
            cube([pocket_len + 2 * wall_min, chute_top_w + 2 * wall_min, eps],
                 center = true);
        translate([0, bore_y + chute_out, chute_bot])
            cube([pocket_len + 2 * wall_min, chute_mouth_d + 2 * wall_min, eps],
                 center = true);
    }
}

module cap_boss_solid(z) {
    hull() {
        translate([x_open - boss_len, cap_boss_y, z]) rotate([0, 90, 0])
            cylinder(d = cap_boss_d, h = boss_len);
        bore_cyl(wall_min, x_open - boss_len, x_open);
    }
}

// --- Cavities -------------------------------------------------------------

module throat_cavity() {
    hull() {
        translate([0, flange_t, port_z]) rotate([90, 0, 0])
            cylinder(d = port_d, h = flange_t + 2);
        translate([0, bore_y, 0])
            cube([pocket_len, bore_d, eps], center = true);
    }
}

module chute_cavity() {
    hull() {
        translate([0, bore_y, chute_top_z])
            cube([pocket_len, chute_top_w, eps], center = true);
        translate([0, bore_y + chute_out, chute_bot])
            cube([pocket_len, chute_mouth_d, eps], center = true);
    }
}

module wall_screw_holes() {
    for (sx = [-1, 1]) for (sz = [-1, 1])
        translate([sx * bolt_dx, flange_t + 1, port_z + sz * bolt_dz])
            rotate([90, 0, 0]) cylinder(d = screw_d, h = flange_t + ring_t + wall_t + 4);
}

module nut_trap_x(z, dir) {
    translate([x_open - trap_x, cap_boss_y, z])
        hull() {
            rotate([0, 90, 0])
                cylinder($fn = 6, d = (nut_af + 0.2) / cos(30), h = nut_h + 0.2,
                         center = true);
            translate([0, 0, dir * 25]) rotate([0, 90, 0])
                cylinder($fn = 6, d = (nut_af + 0.2) / cos(30), h = nut_h + 0.2,
                         center = true);
        }
}

// --- Parts ----------------------------------------------------------------

module dispenser_body() {
    difference() {
        union() {
            flange_plate();
            housing_solid();
            throat_solid();
            chute_solid();
            cap_boss_solid(cap_boss_dz);
            cap_boss_solid(-cap_boss_dz);
        }
        // Drum chamber: open at +X, blind at -X.
        bore_cyl(0, -chamber_len / 2, x_open + 40);
        // Blind journal socket in the -X end wall.
        translate([-chamber_len / 2 - journal_len - 1, bore_y, 0])
            rotate([0, 90, 0]) cylinder(d = journal_d + 0.6, h = journal_len + 1);
        throat_cavity();
        chute_cavity();
        // Port through the flange.
        translate([0, flange_t + 1, port_z]) rotate([90, 0, 0])
            cylinder(d = port_d, h = flange_t + 3);
        wall_screw_holes();
        // Cap screws through the bosses.
        for (sz = [-1, 1])
            translate([x_open - boss_len - 1, cap_boss_y, sz * cap_boss_dz])
                rotate([0, 90, 0]) cylinder(d = screw_d, h = boss_len + 2);
        nut_trap_x(cap_boss_dz, 1);
        nut_trap_x(-cap_boss_dz, -1);
    }
}

module dispenser_drum() {
    difference() {
        union() {
            translate([-drum_len / 2, bore_y, 0]) rotate([0, 90, 0])
                cylinder(d = drum_d, h = drum_len);
            translate([-drum_len / 2 - journal_len, bore_y, 0]) rotate([0, 90, 0])
                cylinder(d = journal_d, h = journal_len);
            translate([drum_len / 2, bore_y, 0]) rotate([0, 90, 0])
                cylinder(d = journal_d, h = x_open + cap_t + 0.8 - drum_len / 2);
            translate([x_open + cap_t + 0.8, bore_y, 0]) rotate([0, 90, 0])
                cylinder($fn = 6, d = shaft_af / cos(30), h = shaft_len);
        }
        // Scoop pocket: flat floor at Z = drum_d/2 - pocket_depth.
        translate([0, bore_y, drum_d / 2 - pocket_depth + drum_d / 2])
            cube([pocket_len, drum_d + 2, drum_d], center = true);
        // Knob retention pilot down the shaft axis.
        translate([x_open + cap_t + 0.8 + shaft_len - knob_pilot_h, bore_y, 0])
            rotate([0, 90, 0]) cylinder(d = knob_pilot_d, h = knob_pilot_h + 1);
    }
}

module dispenser_cap() {
    difference() {
        hull() {
            translate([x_open, bore_y, 0]) rotate([0, 90, 0])
                cylinder(d = bore_d + 2 * wall_min, h = cap_t);
            for (sz = [-1, 1])
                translate([x_open, cap_boss_y, sz * cap_boss_dz]) rotate([0, 90, 0])
                    cylinder(d = cap_boss_d, h = cap_t);
        }
        translate([x_open - 1, bore_y, 0]) rotate([0, 90, 0])
            cylinder(d = journal_d + 0.6, h = cap_t + 2);
        for (sz = [-1, 1])
            translate([x_open - 1, cap_boss_y, sz * cap_boss_dz]) rotate([0, 90, 0])
                cylinder(d = screw_d, h = cap_t + 2);
    }
}

module dispenser_knob() {
    knob_x0 = x_open + cap_t + 1;
    difference() {
        translate([knob_x0, bore_y, 0]) rotate([0, 90, 0])
            cylinder(d = knob_d, h = knob_h);
        for (i = [0 : knob_flutes - 1])
            translate([knob_x0 - 1,
                       bore_y + (knob_d / 2) * cos(i * 360 / knob_flutes),
                       (knob_d / 2) * sin(i * 360 / knob_flutes)])
                rotate([0, 90, 0]) cylinder(d = 9, h = knob_h + 2);
        // Hex socket for the drive shaft.
        translate([knob_x0 - 1, bore_y, 0]) rotate([0, 90, 0])
            cylinder($fn = 6, d = (shaft_af + 0.25) / cos(30), h = shaft_len + 1);
        // Retention screw clearance + counterbore.
        translate([knob_x0 + knob_h - 4, bore_y, 0]) rotate([0, 90, 0])
            cylinder(d = screw_d, h = 6);
        translate([knob_x0 + knob_h - 3, bore_y, 0]) rotate([0, 90, 0])
            cylinder(d = 8, h = 4);
    }
}

module dispenser_ring() {
    difference() {
        translate([0, -(wall_t + ring_t), 0])
            rounded_plate(ring_w, ring_h, port_z, ring_t, flange_r);
        translate([0, 1, port_z]) rotate([90, 0, 0])
            cylinder(d = port_d, h = wall_t + ring_t + 3);
        for (sx = [-1, 1]) for (sz = [-1, 1]) {
            translate([sx * bolt_dx, 1, port_z + sz * bolt_dz]) rotate([90, 0, 0])
                cylinder(d = screw_d, h = wall_t + ring_t + 3);
            // Captive nut pocket opening on the box-interior (-Y) face.
            translate([sx * bolt_dx, -(wall_t + ring_t) - 0.5, port_z + sz * bolt_dz])
                rotate([-90, 0, 0])
                    cylinder($fn = 6, d = (nut_af + 0.2) / cos(30), h = nut_h + 0.7);
        }
    }
}

module dispenser_template() {
    difference() {
        translate([0, -template_t, 0])
            rounded_plate(2 * (bolt_dx + 10),
                          flange_top - (port_z - port_d / 2 - floor_offset - 8),
                          (flange_top + port_z - port_d / 2 - floor_offset - 8) / 2,
                          template_t, flange_r);
        translate([0, 1, port_z]) rotate([90, 0, 0])
            cylinder(d = port_d, h = template_t + 3);
        for (sx = [-1, 1]) for (sz = [-1, 1])
            translate([sx * bolt_dx, 1, port_z + sz * bolt_dz]) rotate([90, 0, 0])
                cylinder(d = screw_d, h = template_t + 3);
        // Engraved floor line: sit this on the box's internal floor level.
        translate([0, -1.5 - template_t, port_z - port_d / 2 - floor_offset])
            cube([2 * (bolt_dx + 10) + 2, 3, 2], center = true);
    }
}

module dispenser_assembly() {
    dispenser_body();
    dispenser_drum();
    dispenser_cap();
    dispenser_knob();
    dispenser_ring();
}
