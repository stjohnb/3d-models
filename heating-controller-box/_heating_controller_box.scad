// =====================================
// Heating controller project box
// Two-part, fully 3D-printed wall enclosure for the ESP32-2432S028R ("CYD")
// heating and hot-water controller that replaces a Danfoss FP720 programmer;
// the schematic and wiring order are in the controller build notes.
// =====================================
// Parts:
//   heating_controller_base -> heating_controller_base.stl
//       Wall-mounted tray with an L-shaped partition rib that keeps the
//       low-voltage CYD bay apart from the mains bay (PSU, relay terminals,
//       WAGO block, toggles, lamps); relay bosses, PSU and WAGO cradles,
//       corner lid-screw posts, wall-screw holes, cable entries, vent slots
//       and a stylus sleeve on the outside of the right-hand (+X) wall.
//   heating_controller_lid  -> heating_controller_lid.stl
//       Faceplate: framed display window with CYD bosses behind it, two
//       keyed Hand-Off-Auto toggle holes, two indicator-lamp holes, locating
//       lip (notched where the partition ribs meet the walls) and four
//       countersunk lid screws.
//
// Orientation: both parts are modelled in print orientation (Z-up), centred
// on X/Y with their bed face at z=0. The base opens toward +Z; the lid lies
// outer face down, so its bosses and lip rise toward +Z.
//
// Layout frame: every position is given in "front view" coordinates -
// looking at the installed box from the room, X right, Y up. The open base
// is viewed from the same side, so it uses them directly; the lid is mirrored
// in X in heating_controller_lid() so its face-down print matches.
//
//   LV bay   : x < rib_x, y > rib_y   (CYD hangs from the lid above it)
//   mains bay: everything else - bottom strip (PSU and WAGO on the floor),
//              right column (toggles and lamps hanging from the lid) and the
//              relay board below the lower toggle, its header kept
//              relay_header_clear from the toggle and its screw terminals
//              facing a wiring channel along the bottom wall
//
// Fixings: every screw goes into an M3 heat-set insert (12 in total) in a
// printed boss or post - 4 CYD bosses on the lid, 4 relay bosses and 4
// corner posts in the base. The printed relay bosses insulate the mains-side
// board from the fixings, so no standoffs are used.
//
// Dimensions marked VERIFY are assumptions; the rest were calipered on
// 23 September 2026.

$fn = 64;

// === Enclosure (mm) ===
inner_w      = 164;   // cavity width (X)
inner_h      = 128;   // cavity height (Y)
inner_d      = 40;    // cavity depth, floor top to lid underside
wall         = 2.4;   // side wall thickness
floor_t      = 3;     // base floor thickness (holds the wall-screw countersinks)
corner_r     = 4;     // outer corner radius
lid_t        = 3.0;   // lid plate thickness (backs the CYD insert pockets)
lip_t        = 1.6;   // locating lip thickness
lip_d        = 4;     // locating lip depth into the base
lip_clear    = 0.3;   // lip to cavity wall clearance, per side

// === Heat-set inserts (every fixing) ===
// M3 heat-set insert, 4.6 mm OD, 4 to 5.7 mm long. Set insert_hole_d = 2.6
// for a self-tapping M3 pilot when printing without inserts.
insert_hole_d  = 4.0;
insert_depth   = 6;    // pocket depth below the boss or post top
insert_chamfer = 0.5;  // entry chamfer at the pocket mouth
lid_skin       = 1.2;  // minimum lid left behind a CYD insert pocket

// --- Lid screws (countersunk M3 into inserts in the corner posts) ---
post_r       = 4;     // 8 mm posts leave a full wall round the chamfered pocket
post_fuse    = 0.3;   // post overlap into the walls so it fuses
lid_screw_l  = 10;    // M3 x 10 countersunk
screw_clear  = 3.4;   // lid through hole
screw_head   = 6.8;   // countersink diameter, ISO M3 countersunk head

// === Partition rib between the LV bay and the mains bay ===
rib_t        = 2;
rib_x        = 14;    // vertical rib centre (right edge of the LV bay)
rib_y        = -12;   // horizontal rib centre (bottom edge of the LV bay)
rib_gap      = 0.5;   // rib top to lid underside
notch_x      = -2;    // pass-through for the CYD pigtail and PSU 5 V leads
notch_w      = 20;
notch_sill   = 12;    // notch floor above the base floor

// === CYD (ESP32-2432S028R) - measured ===
cyd_hole_x    = 78;   // mounting hole pitch, long side
cyd_hole_y    = 42;   // mounting hole pitch, short side
cyd_hole_d    = 3;
cyd_pcb_l     = 86.5; // PCB outline (VERIFY; published spec)
cyd_pcb_w     = 50.5;
cyd_pcb_t     = 1.6;
cyd_thickness = 9;    // absolute, glass front to tallest rear component
cyd_display_h = 4;    // glass/frame height above the PCB face (VERIFY)
cyd_module_l  = 69;   // display module outline, frame included
cyd_module_w  = 50;
cyd_boss_d    = 7.5;  // 8 would clear the display module by only 0.25 mm
cyd_boss_gap  = 0.3;  // glass to lid underside
cyd_screw_l   = 6;    // M3 x 6 from the board side
cyd_cx        = -36;  // CYD centre in the layout frame
cyd_cy        = 22;

// --- Display window: the frame hides the module edge; the 2.8" active area
//     is about 57.6 x 43.2, so the default shows it with a small margin.
window_l      = 59;
window_w      = 45;
window_r      = 2;
window_off_x  = 0;    // shift if the glass is not centred on the holes (VERIFY)
window_off_y  = 0;

// === Hand-Off-Auto toggles (2x XURUI XT-13A) - body and hole measured ===
toggle_body_l = 30;   // along the throw direction (Y)
toggle_body_w = 15;
toggle_depth  = 32;   // behind the panel, terminals included
toggle_hole_d = 12;   // panel hole for the bushing
toggle_key_depth = 1; // key tab into the hole at 12 o'clock; 0 removes it
toggle_key_w  = 1.5;  // key tab width (VERIFY: estimated from a photo)
toggle_plate_w = 12;  // legend plate footprint, clearance only (VERIFY)
toggle_plate_h = 31;
toggle_plate_boss_d = 18;
toggle_x      = 32;
row_cy        = 28;   // rows sit at row_cy +/- row_dy:
row_dy        = 17;   // heating above (y=45), hot water below (y=11)

// === 230 V panel indicator lamps - not yet in hand ===
lamp_hole_d   = 10;   // typical 8 or 10 mm cut-out; confirm on arrival
lamp_bezel_d  = 14;   // clearance only (VERIFY)
lamp_x        = 52;

// === 2-channel relay board - holes measured ===
relay_hole_x  = 43.7;
relay_hole_y  = 32.5;
relay_hole_d  = 3;
relay_board_l = 50;   // outline (VERIFY)
relay_board_w = 38;
relay_board_t = 17;   // full height at the thickest, PCB included
relay_pcb_t   = 1.6;  // (VERIFY)
relay_boss_d  = 8;
relay_boss_h  = 8;    // clears the solder side and the wiring under the board
relay_screw_l = 6;    // M3 x 6
relay_cx      = 50;   // right of the vertical rib, below the lower toggle
relay_cy      = -33;  // header edge toward +Y, screw terminals toward -Y
relay_terminal_clear = 12;  // terminal edge to the -Y wall, to wire the terminals
relay_header_clear   = 10;  // header edge to the lower toggle, keeps the 5 V and GPIO
                            // leads away from its 230 V terminals

// === Hi-Link HLK-10M05B PSU on its stripboard - PSU measured ===
psu_l         = 62;   // stripboard assembly incl. 2x2 AC terminal (VERIFY; PSU alone 47)
psu_w         = 30;   // (VERIFY; PSU alone 28)
psu_h         = 24;
psu_cx        = -45;
psu_cy        = -35;

// === WAGO 221 5-way lever block - measured ===
wago_l        = 27;
wago_w        = 22;
wago_h        = 15;
wago_cx       = 6;    // between the PSU and the relay board
wago_cy       = -42;

// --- Cradles: four L-shaped corner retainers per footprint ---
cradle_h      = 8;
cradle_arm    = 8;
cradle_t      = 1.6;
cradle_clear  = 0.4;

// === Cable entry ===
cable_floor    = true;   // rectangular knockout through the floor (cable from the wall)
cable_floor_l  = 16;
cable_floor_w  = 10;
cable_floor_x  = 70;
cable_floor_y  = 22;
cable_wall     = false;  // round hole in the right (+X) wall for a surface cable
cable_wall_d   = 8;
cable_wall_y   = -45;    // beside the relay board, below the stylus sleeve

// === Wall fixing (countersunk from the cavity side) ===
mount_hole_d   = 4.5;
mount_head_d   = 9;
mount_holes    = [[-62, 50], [62, 50], [-62, -38], [62, -38]];

// === Ventilation slots in the +/-Y walls over the PSU column ===
vents          = true;
vent_w         = 2;     // narrow enough to keep fingers out of a mains box
vent_pitch     = 5;
vent_x0        = -70;
vent_x1        = -20;
vent_z0        = 5;     // slot bottom above the floor
vent_z1        = 31;    // slot top above the floor, below the lid lip

// === Stylus sleeve (the CYD's DS-style stylus) - stylus measured ===
stylus_sleeve       = true;
stylus_l            = 87.3;  // overall length
stylus_cap_l        = 12;    // cap length along the axis, about 7.7 across
stylus_bore_d       = 5.6;   // shaft bore (4.89 shaft)
stylus_cap_d        = 8.4;   // cap counterbore
stylus_cap_depth    = 8;     // leaves 4 mm of the cap proud to grip
stylus_sleeve_w     = 12.4;  // sleeve block size in X and Z
stylus_sleeve_top_y = 55;    // sleeve top edge in the layout frame

// === Derived ===
outer_w    = inner_w + 2 * wall;
outer_h    = inner_h + 2 * wall;
inner_r    = max(0.5, corner_r - wall);
base_h     = floor_t + inner_d;
post_x     = inner_w/2 - post_r + post_fuse;
post_y     = inner_h/2 - post_r + post_fuse;
cyd_boss_h = cyd_display_h + cyd_boss_gap;
rib_h      = inner_d - rib_gap;
cs_h       = (mount_head_d - mount_hole_d) / 2;   // 90 degree countersink depth
lip_notch_w = rib_t + 2 * lip_clear + 1;
cyd_insert_depth  = min(insert_depth, cyd_boss_h + lid_t - lid_skin);
post_insert_depth = max(insert_depth, lid_screw_l - lid_t + 1);
min_boss_d = min(cyd_boss_d, relay_boss_d, 2 * post_r);
sleeve_l   = stylus_l - (stylus_cap_l - stylus_cap_depth) + 1;

assert(window_l < cyd_module_l && window_w < cyd_module_w,
       "window must stay inside the display module outline to hide its edge");
assert(cs_h < floor_t, "floor too thin for the wall-screw countersink");
assert(lid_t + toggle_depth < lid_t + inner_d, "toggles deeper than the cavity");

// --- Toggles and lamps ---
assert(toggle_key_depth >= 0 && toggle_key_depth < toggle_hole_d/2
       && toggle_key_w < toggle_hole_d,
       "toggle key tab must fit inside the toggle hole");
assert(2 * row_dy >= toggle_plate_h + 2,
       "toggle legend plates overlap: increase row_dy");
assert(lamp_x - toggle_x >= toggle_plate_boss_d/2 + lamp_bezel_d/2 + 1,
       "lamp bezels overlap the toggle legend plates");
assert(row_cy + row_dy + toggle_plate_h/2 <= inner_h/2 + wall,
       "upper toggle legend plate runs off the lid face");
assert(row_cy - row_dy - toggle_body_l/2 > rib_y + rib_t/2,
       "lower toggle body hits the partition rib");
assert(row_cy + row_dy + toggle_body_l/2 < inner_h/2 - lip_clear - lip_t,
       "upper toggle body hits the lid lip");
assert(vent_z0 > 0 && vent_z1 <= inner_d - lip_d,
       "vent slots run into the floor or the lid lip");

// --- Heat-set inserts ---
assert(insert_hole_d >= 2.4 && insert_hole_d <= min_boss_d - 2.5,
       "insert_hole_d must leave a wall in every boss and post");
assert(min_boss_d >= 7, "insert bosses and posts must be at least 7 mm across");
assert(insert_depth >= 6, "insert pockets must be at least 6 mm deep");
assert(cyd_insert_depth >= 6,
       "CYD insert pocket under 6 mm: raise cyd_display_h or lid_t");
assert(cyd_screw_l - cyd_pcb_t <= cyd_insert_depth,
       "CYD screws bottom out in their insert pockets");
assert(relay_screw_l - relay_pcb_t <= insert_depth,
       "relay screws bottom out in their insert pockets");
assert(lid_screw_l - lid_t <= post_insert_depth - 0.5,
       "lid screws bottom out in the corner posts");
assert(post_insert_depth <= inner_d - 2, "corner post insert pockets too deep");
assert(insert_depth <= relay_boss_h + floor_t - 1.5,
       "relay insert pockets break through the floor");
assert(cyd_hole_x/2 - cyd_boss_d/2 >= cyd_module_l/2 + 0.5,
       "CYD bosses hit the display module");
assert(floor_t + relay_boss_h + relay_board_t <= floor_t + inner_d - 1,
       "relay board on its bosses hits the lid");
assert((screw_head - screw_clear)/2 < lid_t, "lid too thin for the countersink");

// --- Floor layout ---
assert(relay_cy - relay_board_w/2 + inner_h/2 >= relay_terminal_clear,
       "no room to wire the relay screw terminals: raise relay_cy");
assert(relay_cx - relay_board_l/2 > rib_x + rib_t/2
       || relay_cy + relay_board_w/2 < rib_y - rib_t/2,
       "relay board hits the partition rib");
assert(relay_cx + relay_board_l/2 <= inner_w/2 - 2,
       "relay board runs into the right-hand wall");
assert(relay_cy + relay_board_w/2 + relay_header_clear
       <= row_cy - row_dy - toggle_body_l/2,
       "relay header too close to the lower toggle's mains terminals: lower relay_cy");
assert(psu_cx + psu_l/2 + cradle_clear + cradle_t
       < wago_cx - wago_l/2 - cradle_clear - cradle_t,
       "PSU and WAGO cradles overlap");
assert(wago_cx + wago_l/2 + cradle_clear + cradle_t < relay_cx - relay_board_l/2,
       "WAGO cradle runs under the relay board");

// --- Stylus sleeve ---
assert(stylus_bore_d > 4.89 && stylus_bore_d < stylus_cap_d && stylus_cap_d > 7.65,
       "stylus bores must clear the 4.89 mm shaft and the 7.65 mm cap");
assert(stylus_cap_depth < stylus_cap_l,
       "stylus cap would sit at or below the sleeve rim");
assert(stylus_sleeve_top_y <= outer_h/2 - corner_r,
       "stylus sleeve runs into the rounded top corner");
assert(stylus_sleeve_top_y - sleeve_l >= -outer_h/2,
       "stylus sleeve runs past the bottom of the box");
assert(stylus_cap_d/2 + 0.6 + 1.2 <= stylus_sleeve_w/2,
       "stylus sleeve too thin around the cap counterbore");
assert(!(stylus_sleeve && cable_wall)
       || cable_wall_y + cable_wall_d/2 < stylus_sleeve_top_y - sleeve_l - 2,
       "wall cable hole collides with the stylus sleeve");

// === Modules ===

// Rounded-rect vertical prism: hull of four corner cylinders.
// Centred on X/Y, base at z=0.
module rbox(w, l, h, r) {
    hull()
        for (sx = [-1, 1], sy = [-1, 1])
            translate([sx * (w/2 - r), sy * (l/2 - r), 0])
                cylinder(r = r, h = h);
}

// Heat-set insert pocket: blind hole running along -Z from its mouth at z=0,
// with an entry chamfer. Both extend 0.01 above the mouth.
module insert_hole(depth) {
    translate([0, 0, -depth])
        cylinder(d = insert_hole_d, h = depth + 0.01);
    translate([0, 0, -insert_chamfer])
        cylinder(d1 = insert_hole_d, d2 = insert_hole_d + 2 * insert_chamfer,
                 h = insert_chamfer + 0.01);
}

// Teardrop with its apex toward +Y, cut flat 0.6 above the circle, so a
// horizontal bore prints without supports.
module flat_teardrop(d) {
    intersection() {
        hull() {
            circle(d = d);
            rotate(45) square(d/2);
        }
        translate([-d, -d]) square([2 * d, 1.5 * d + 0.6]);
    }
}

// Toggle panel cut-out, matching the legend plate: round hole with a key tab
// of lid material intruding at 12 o'clock.
module toggle_cutout() {
    difference() {
        circle(d = toggle_hole_d);
        translate([-toggle_key_w/2, toggle_hole_d/2 - toggle_key_depth])
            square([toggle_key_w, toggle_key_depth + 1]);
    }
}

// Four L-shaped corner retainers around an l x w footprint centred at
// (cx, cy), standing on the base floor.
module cradle(cx, cy, l, w, h) {
    hl = l/2 + cradle_clear;
    hw = w/2 + cradle_clear;
    translate([cx, cy, floor_t - 0.01])
        for (sx = [-1, 1], sy = [-1, 1]) {
            // arm along X, outside the footprint in Y
            translate([sx * (hl + cradle_t - (cradle_arm + cradle_t)/2),
                       sy * (hw + cradle_t/2), h/2])
                cube([cradle_arm + cradle_t, cradle_t, h], center = true);
            // arm along Y, outside the footprint in X
            translate([sx * (hl + cradle_t/2),
                       sy * (hw - cradle_arm/2), h/2])
                cube([cradle_t, cradle_arm, h], center = true);
        }
}

module corner_positions() {
    for (sx = [-1, 1], sy = [-1, 1])
        translate([sx * post_x, sy * post_y, 0]) children();
}

module relay_positions() {
    for (sx = [-1, 1], sy = [-1, 1])
        translate([relay_cx + sx * relay_hole_x/2,
                   relay_cy + sy * relay_hole_y/2, 0]) children();
}

module cyd_positions() {
    for (sx = [-1, 1], sy = [-1, 1])
        translate([cyd_cx + sx * cyd_hole_x/2,
                   cyd_cy + sy * cyd_hole_y/2, 0]) children();
}

// L-shaped partition: horizontal rib from the left wall to the vertical rib,
// vertical rib from the horizontal rib up to the top wall. Both fuse into the
// walls by post_fuse.
module partition() {
    x_left = -inner_w/2 - post_fuse;
    x_right = rib_x + rib_t/2;
    y_top = inner_h/2 + post_fuse;
    y_bot = rib_y - rib_t/2;
    translate([0, 0, floor_t - 0.01]) difference() {
        union() {
            translate([x_left, y_bot, 0])
                cube([x_right - x_left, rib_t, rib_h + 0.01]);
            translate([rib_x - rib_t/2, y_bot, 0])
                cube([rib_t, y_top - y_bot, rib_h + 0.01]);
        }
        // Pass-through notch for the CYD pigtail and PSU 5 V leads
        translate([notch_x - notch_w/2, y_bot - 1, notch_sill])
            cube([notch_w, rib_t + 2, rib_h + 2]);
    }
}

// Vertical stylus sleeve on the outside of the +X wall, standing on the wall
// face. Its bores run along Y and stay wholly outside the box wall, so the
// sleeve never opens into the mains bay. The shaft bore is open at the
// bottom to push a stuck stylus out; the cap drops into a counterbore at the
// top and stands proud of it.
module stylus_sleeve() {
    x0 = outer_w/2 - 0.8;
    bore_x = x0 + stylus_sleeve_w/2;
    bore_z = stylus_sleeve_w/2;
    difference() {
        translate([x0, stylus_sleeve_top_y - sleeve_l, 0])
            cube([stylus_sleeve_w, sleeve_l, stylus_sleeve_w]);
        // rotate([90, 0, 0]) maps the profile's +Y to +Z and extrudes toward -Y
        translate([bore_x, stylus_sleeve_top_y + 1, bore_z])
            rotate([90, 0, 0]) {
                linear_extrude(sleeve_l + 2) flat_teardrop(stylus_bore_d);
                linear_extrude(stylus_cap_depth + 1) flat_teardrop(stylus_cap_d);
            }
    }
}

// Base tray: floor at z=0, opening toward +Z.
module heating_controller_base() {
    difference() {
        union() {
            difference() {
                rbox(outer_w, outer_h, base_h, corner_r);
                translate([0, 0, floor_t])
                    rbox(inner_w, inner_h, inner_d + 1, inner_r);
            }
            // Corner posts for the lid screws (fused into the walls)
            corner_positions()
                translate([0, 0, floor_t - 0.01])
                    cylinder(r = post_r, h = inner_d + 0.01);
            partition();
            // Relay board bosses: the board screws straight onto them
            relay_positions()
                translate([0, 0, floor_t - 0.01])
                    cylinder(d = relay_boss_d, h = relay_boss_h + 0.01);
            // PSU and WAGO cradles
            cradle(psu_cx, psu_cy, psu_l, psu_w, cradle_h);
            cradle(wago_cx, wago_cy, wago_l, wago_w, min(cradle_h, wago_h - 3));
        }

        // Lid screw inserts in the corner post tops
        corner_positions()
            translate([0, 0, base_h]) insert_hole(post_insert_depth);

        // Relay board inserts in the boss tops, stopping above the floor
        relay_positions()
            translate([0, 0, floor_t + relay_boss_h]) insert_hole(insert_depth);

        // Wall-fixing holes: through hole plus a countersink that opens into
        // the cavity, since the screws are driven from inside the open base.
        for (p = mount_holes)
            translate([p[0], p[1], 0]) {
                translate([0, 0, -1]) cylinder(d = mount_hole_d, h = floor_t + 2);
                translate([0, 0, floor_t - cs_h])
                    cylinder(d1 = mount_hole_d, d2 = mount_head_d + 2, h = cs_h + 1);
            }

        // Cable entries
        if (cable_floor)
            translate([cable_floor_x, cable_floor_y, -1])
                rbox(cable_floor_l, cable_floor_w, floor_t + 2, 2);
        if (cable_wall)
            translate([inner_w/2 + wall/2, cable_wall_y, floor_t + cable_wall_d/2 + 1])
                rotate([0, 90, 0])
                    cylinder(d = cable_wall_d, h = wall + 2, center = true);

        // Vent slots through both long walls
        if (vents)
            for (sy = [-1, 1], x = [vent_x0 : vent_pitch : vent_x1])
                translate([x, sy * (inner_h/2 + wall/2), floor_t + (vent_z0 + vent_z1)/2])
                    cube([vent_w, wall + 2, vent_z1 - vent_z0], center = true);
    }

    // Added after the cuts, so the sleeve bores never touch the +X wall
    if (stylus_sleeve) stylus_sleeve();
}

// Lid in the front-view frame: outer face at z=0, features rising toward +Z.
// The outer face carries only the window, the holes and the countersinks, so
// the toggle legend plates and lamp bezels sit on flat material.
module lid_frame() {
    difference() {
        union() {
            rbox(outer_w, outer_h, lid_t, corner_r);

            // Locating lip inside the cavity walls, notched around the corner
            // posts and where the partition ribs meet the walls.
            translate([0, 0, lid_t - 0.01])
                difference() {
                    rbox(inner_w - 2 * lip_clear, inner_h - 2 * lip_clear,
                         lip_d + 0.01, max(0.5, inner_r - lip_clear));
                    translate([0, 0, -1])
                        rbox(inner_w - 2 * (lip_clear + lip_t),
                             inner_h - 2 * (lip_clear + lip_t),
                             lip_d + 3, max(0.5, inner_r - lip_clear - lip_t));
                    corner_positions()
                        translate([0, 0, -1])
                            cylinder(r = post_r + lip_clear, h = lip_d + 3);
                    // vertical rib meets the top (+Y) wall
                    translate([rib_x - lip_notch_w/2, inner_h/2 - lip_t - lip_clear - 1, -1])
                        cube([lip_notch_w, lip_t + lip_clear + 2, lip_d + 3]);
                    // horizontal rib meets the left (-X) wall
                    translate([-inner_w/2 - 1, rib_y - lip_notch_w/2, -1])
                        cube([lip_t + lip_clear + 2, lip_notch_w, lip_d + 3]);
                }

            // CYD bosses: the glass sits cyd_boss_gap behind the lid
            cyd_positions()
                translate([0, 0, lid_t - 0.01])
                    cylinder(d = cyd_boss_d, h = cyd_boss_h + 0.01);
        }

        // Display window
        translate([cyd_cx + window_off_x, cyd_cy + window_off_y, -1])
            rbox(window_l, window_w, lid_t + 2, window_r);

        // CYD inserts: open at the boss tips and run toward the lid face,
        // leaving at least lid_skin behind them
        cyd_positions()
            translate([0, 0, lid_t + cyd_boss_h]) insert_hole(cyd_insert_depth);

        // Keyed toggle bushings and lamp bezels, one row per circuit
        for (sy = [-1, 1]) {
            translate([toggle_x, row_cy + sy * row_dy, -1])
                linear_extrude(lid_t + 2) toggle_cutout();
            translate([lamp_x, row_cy + sy * row_dy, -1])
                cylinder(d = lamp_hole_d, h = lid_t + 2);
        }

        // Lid screws, countersunk on the outer face
        corner_positions() {
            translate([0, 0, -1]) cylinder(d = screw_clear, h = lid_t + 2);
            translate([0, 0, -0.01])
                cylinder(d1 = screw_head, d2 = screw_clear,
                         h = (screw_head - screw_clear)/2);
        }
    }
}

// Lid in print orientation: outer face on the bed. Mirrored so the layout
// reads correctly from the front once the lid is turned over onto the base.
module heating_controller_lid() {
    mirror([1, 0, 0]) lid_frame();
}
