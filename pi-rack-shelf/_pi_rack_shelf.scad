// =====================================
// Raspberry Pi 19" rack-mount shelf (2U, four Pis on their long edge)
// Two halves that fit a 256 mm Bambu Lab A1 bed and bolt together through
// face-to-face flanges at the centre split.
// =====================================
// Parts:
//   shelf_2u_pi   -> pi_rack_shelf_2u_pi.stl    (left half, four Pis standing on a long edge)
//   shelf_2u_tray -> pi_rack_shelf_2u_tray.stl  (right half, plain open tray)
//
// Coordinates: Z-up, as mounted. X runs left to right seen from the rack
// front, centred on the rack; the faceplate front is y = 0 and the shelf
// runs back along +Y; the floor underside is z = 0. Every half is modelled
// in its assembled position and prints floor-down as exported, no supports.
//
// Each cased Pi stands on its long edge with its Ethernet/USB-A end against
// its own faceplate window. The cable side (USB-C power, micro-HDMI) faces
// UP and the top of the shelf is open: nothing goes over the Pis. The
// roughly 19 mm of headroom above a Pi (panel height less floor less case
// width) is enough for right-angle plugs, whose bodies stand only a few
// millimetres proud of the case; min_headroom asserts at least 15 mm.
// Both halves are boxed: a full-width rear wall, and side walls that drop
// from panel height at the front to box_wall_h at the rear.

// ---- Rack (EIA-310, mm) ----
rack_panel_w    = 482.6;   // overall faceplate width
rack_hole_span  = 465.1;   // mounting hole centres, left to right
rack_opening_w  = 450.85;  // clear opening between the rails
rack_u          = 44.45;   // one rack unit
panel_clearance = 0.8;     // faceplate is this much shorter than nominal
slot_w          = 10.5;    // ear slot width (X), M6 with sideways play
slot_h          = 7;       // ear slot height (Z)
body_side_gap   = 2.4;     // shelf body to rail opening, per side

// ---- Shelf body ----
face_t     = 4;    // faceplate and ear thickness
floor_t    = 3;    // shelf floor thickness
wall_t     = 3;    // outer side wall and rear wall thickness
lip_h      = 14;   // tray front lip height
box_wall_h = 40;   // outer side wall, joint flange and rear wall height at the rear
gusset_run = 25;   // side walls stay full panel height this far behind the faceplate
depth      = 160;  // overall depth (Y)

// ---- Split and bolted joint (M4 bolt, washer and hex nut in a trap) ----
split_x         = 0;     // split plane (X); both halves are 241.3 mm wide
joint_gap       = 0.1;   // each flange face stands back this far from the split
flange_head_t   = 4;     // left half's flange (bolt heads bear on it)
flange_nut_t    = 6;     // right half's flange (carries the nut traps)
bolt_d          = 4.5;   // M4 clearance hole
nut_af          = 7.2;   // M4 nut across flats, with fit
nut_trap_depth  = 3.4;   // trap depth in the right flange's far face
bolt_front_y    = 18;    // front bolt pair, distance behind the faceplate front
bolt_rear_inset = 15;    // rear bolt, distance in front of the rear edge (at box_wall_h / 2)
bolt_zs         = [50, 75];  // front bolt heights
bolt_head_clear = 10;    // least free X between the Pi half's flange and the last slot's fin (head and washer)

// ---- The cased Pi (generic size, standing on its long edge) ----
pi_case_w = 66;   // case width; stands vertically
pi_case_h = 30;   // case height; becomes the slot width (X)
pi_d      = 94;   // case depth (port end to SD end)
pi_fit    = 0.5;  // slot clearance per side
pi_count  = 4;    // Pis on the Pi half, 1 to 4
min_air_gap  = 10;  // least air between slot fins, and between the end slots and the walls
min_headroom = 15;  // least open height above a Pi, for right-angle plugs

// ---- Pi slot ----
fin_t          = 2.5; // retaining fin thickness
fin_h          = 25;  // retaining fin and rear stop height above the floor
fin_seg_l      = 30;  // length of the front and rear fins; the middle stays open
stop_t         = 3;   // rear stop thickness
sd_gap         = 30;  // gap between the rear stop tabs (SD card access)
window_inset   = 2;   // faceplate overlap on each side of the case end
window_sill    = 3;   // faceplate overlap under the case end
window_top_gap = 1;   // window top above the case
window_chamfer = 12;  // 45 degree top corners, shortens the printed bridge
rear_notch_w   = 20;  // cable notch in the rear wall, per slot, open at the top
rear_notch_d   = 12;  // cable notch depth
vents          = true;
vent_w         = 4;
vent_l         = 60;
vent_pitch     = 10;
rear_vent_w     = 4;   // rear wall vent slit width (obround, vertical)
rear_vent_l     = 16;  // rear wall vent slit length
rear_vent_pitch = 12;  // rear wall vent slit pitch

// ---- Derived ----
eps        = 0.01;
body_half  = rack_opening_w / 2 - body_side_gap;
pocket_d   = pi_d + 2 * pi_fit;
pi_slot_w  = pi_case_h + 2 * pi_fit;
panel_h    = 2 * rack_u - panel_clearance;
window_h   = pi_case_w + window_top_gap - window_sill;
headroom   = panel_h - floor_t - pi_case_w;

// Equal air gaps at both ends and between slots. Each slot cell is the
// pocket plus a fin each side; the layout runs from the outer wall's inner
// face to the Pi half's flange face.
x_in0   = -body_half + wall_t;
x_in1   = split_x - joint_gap - flange_head_t;
cell_w  = pi_slot_w + 2 * fin_t;
air_gap = (x_in1 - x_in0 - pi_count * cell_w) / (pi_count + 1);

function slot_xs() = [for (i = [0 : pi_count - 1])
                        x_in0 + air_gap * (i + 1) + cell_w * i + fin_t];
function bolts(depth) = [for (z = bolt_zs) [bolt_front_y, z],
                         [depth - bolt_rear_inset, box_wall_h / 2]];
function slot_zs() = [for (i = [0 : 1]) for (z = [6.35, 38.1])
                        i * rack_u + z - panel_clearance / 2];

assert(1 <= pi_count && pi_count <= 4, "pi_count must be 1 to 4");
assert(air_gap >= max(min_air_gap, bolt_head_clear), "air gap around the Pi slots below min_air_gap or bolt_head_clear");
assert(headroom >= min_headroom, "headroom above the Pis below min_headroom");
assert(rack_panel_w / 2 + abs(split_x) <= 250, "a half is wider than 250 mm");
assert(depth <= 250, "shelf deeper than 250 mm");
assert(depth >= face_t + pocket_d + stop_t + wall_t, "shelf too shallow for the Pi slot");
assert(box_wall_h / 2 - nut_af / 2 / cos(30) >= floor_t, "rear bolt's nut trap reaches the floor");
assert(box_wall_h >= floor_t + rear_notch_d + rear_vent_l + 4, "box_wall_h too low for the rear wall's cable notch and vent slits");
assert(box_wall_h <= panel_h, "box_wall_h above the faceplate height");
assert(sd_gap <= pi_slot_w, "sd_gap wider than the slot");
assert(rear_notch_w <= pi_slot_w, "cable notch wider than the slot");
assert(window_h >= window_chamfer, "window shorter than its chamfered corners");
assert(pi_slot_w - 2 * window_inset >= 2 * window_chamfer, "window narrower than its chamfered corners");
assert(floor_t + window_sill + window_h + 4 <= panel_h, "window too tall for the faceplate");

// ---- Helpers ----
module box(x1, x2, y1, y2, z1, z2)
    translate([min(x1, x2), y1, z1]) cube([abs(x2 - x1), y2 - y1, z2 - z1]);

// Side wall / joint flange: full panel height behind the faceplate, sloping
// to box_wall_h at the rear. Occupies x = 0..t.
module side_wall(depth, t)
    rotate([90, 0, 90]) linear_extrude(t)
        polygon([[0, 0], [depth, 0], [depth, box_wall_h],
                 [face_t + gusset_run, panel_h], [0, panel_h]]);

// Horizontal obround ear slot through the faceplate, centred on the origin.
module rack_slot()
    rotate([-90, 0, 0]) translate([0, 0, -1]) linear_extrude(face_t + 2) hull() {
        translate([-(slot_w - slot_h) / 2, 0]) circle(d = slot_h);
        translate([ (slot_w - slot_h) / 2, 0]) circle(d = slot_h);
    }

module hex_prism(af, h)
    linear_extrude(h)
        polygon([for (i = [0 : 5]) (af / 2 / cos(30)) * [cos(60 * i), sin(60 * i)]]);

// Port window through the faceplate; origin at its lower-left corner, on the
// faceplate rear face.
module window_cutter(w, h)
    translate([0, 1, 0]) rotate([90, 0, 0]) linear_extrude(face_t + 2)
        polygon([[0, 0], [w, 0], [w, h - window_chamfer], [w - window_chamfer, h],
                 [window_chamfer, h], [0, h - window_chamfer]]);

// Slot origin: left front corner of the slot, on the faceplate rear face, at
// floor-top height. Front and rear fins on both sides leave the middle open.
module pi_slot_add() {
    sw  = pi_slot_w;
    tab = (sw - sd_gap) / 2;
    translate([0, -eps, -eps]) {
        for (x = [-fin_t, sw]) {
            translate([x, 0, 0]) cube([fin_t, fin_seg_l, fin_h]);
            translate([x, pocket_d - fin_seg_l, 0]) cube([fin_t, fin_seg_l + stop_t, fin_h]);
        }
        // rear stop tabs with an SD-card gap between them
        translate([-fin_t, pocket_d, 0]) cube([fin_t + tab, stop_t, fin_h]);
        translate([sw - tab, pocket_d, 0]) cube([tab + fin_t, stop_t, fin_h]);
    }
}

module pi_slot_cut() {
    sw = pi_slot_w;
    n  = max(1, floor((sw - 10) / vent_pitch));
    span = (n - 1) * vent_pitch + vent_w;
    translate([window_inset, 0, window_sill])
        window_cutter(sw - 2 * window_inset, window_h);
    if (vents)
        for (i = [0 : n - 1])
            translate([(sw - span) / 2 + i * vent_pitch + vent_w / 2,
                       (pocket_d - vent_l) / 2, -floor_t - 1])
                linear_extrude(floor_t + 2) hull() {
                    translate([0, vent_w / 2]) circle(d = vent_w);
                    translate([0, vent_l - vent_w / 2]) circle(d = vent_w);
                }
}

// One vertical obround vent slit through the rear wall, centred at cx.
module rear_vent(cx, depth)
    translate([cx, depth + 1, floor_t + 2]) rotate([90, 0, 0])
        linear_extrude(wall_t + 2) hull() {
            translate([0, rear_vent_w / 2]) circle(d = rear_vent_w);
            translate([0, rear_vent_l - rear_vent_w / 2]) circle(d = rear_vent_w);
        }

// Rear wall cuts for one slot at slot-left X: cable notch open at the top
// and, with vents, two vent slits below it.
module rear_wall_cut(x, depth) {
    cx = x + pi_slot_w / 2;
    translate([cx - rear_notch_w / 2, depth - wall_t - 1, box_wall_h - rear_notch_d])
        cube([rear_notch_w, wall_t + 2, rear_notch_d + 1]);
    if (vents)
        for (dx = [-1, 1]) rear_vent(cx + dx * rear_vent_pitch / 2, depth);
}

// Tray rear vents, spread evenly across the inner width.
module tray_rear_cut(xin, xbody, depth) {
    lo = min(xin + flange_nut_t, xbody - wall_t);
    hi = max(xin + flange_nut_t, xbody - wall_t);
    n  = floor((hi - lo - 10) / rear_vent_pitch) + 1;
    for (i = [0 : n - 1])
        rear_vent((lo + hi) / 2 + (i - (n - 1) / 2) * rear_vent_pitch, depth);
}

// One half. side = -1 (left of the split) or +1 (right). slots is a list of
// slot-left X values. tray = true swaps the full-height faceplate for a low
// front lip plus a full-height ear.
module shelf_half(depth, side, slots, tray = false) {
    ph     = panel_h;
    xin    = split_x + side * joint_gap;   // joint face
    xbody  = side * body_half;             // outer edge of the shelf body
    xpanel = side * rack_panel_w / 2;      // outer edge of the ear
    ft     = side < 0 ? flange_head_t : flange_nut_t;

    difference() {
        union() {
            if (tray) {
                box(xin, xbody, 0, face_t, 0, lip_h);
                box(xbody - side * wall_t, xpanel, 0, face_t, 0, ph);
            } else {
                box(xin, xpanel, 0, face_t, 0, ph);
            }
            box(xin, xbody, 0, depth, 0, floor_t);
            box(xin, xbody, depth - wall_t, depth, 0, box_wall_h);
            translate([min(xbody, xbody - side * wall_t), 0, 0]) side_wall(depth, wall_t);
            translate([min(xin, xin + side * ft), 0, 0]) side_wall(depth, ft);
            for (x = slots)
                translate([x, face_t, floor_t]) pi_slot_add();
        }
        for (z = slot_zs())
            translate([side * rack_hole_span / 2, 0, z]) rack_slot();
        for (b = bolts(depth)) {
            translate([xin, b[0], b[1]]) rotate([0, 90, 0])
                cylinder(d = bolt_d, h = 2 * (flange_nut_t + 2), center = true);
            if (side > 0)
                translate([xin + ft - nut_trap_depth, b[0], b[1]]) rotate([0, 90, 0])
                    hex_prism(nut_af, nut_trap_depth + 1);
        }
        for (x = slots) {
            translate([x, face_t, floor_t]) pi_slot_cut();
            rear_wall_cut(x, depth);
        }
        if (tray && vents) tray_rear_cut(xin, xbody, depth);
    }
}

module shelf_2u_pi()   shelf_half(depth, -1, slot_xs());
module shelf_2u_tray() shelf_half(depth,  1, [], tray = true);
