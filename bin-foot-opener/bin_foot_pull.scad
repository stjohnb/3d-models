// =====================================
// Bin Foot Opener
// Toe-operated pull for a pull-out kitchen bin drawer
//
// Coordinate convention: x runs through the panel, x = 0 is the panel's back
// face and +x points out into the room; y is in-use up, y = 0 is the panel's
// bottom edge; extrusion runs along +z = bracket width. A single 2D profile
// is linear_extrude()d along the width, so the exported STL is simultaneously
// print-oriented (every face a vertical wall, no supports) and upright in the
// viewer, the scanning-rig/phone_stand.scad pattern. The toe lip is
// intentionally recessed behind the front face, so base_run must not exceed
// the actual panel thickness.
//
// Two triangular end gussets cannot print without support in this orientation
// (a gusset at one end of the width sits on the bed; its twin at the other
// end is a horizontal island floating in mid-air). A single full-width
// triangular web across the base/lip corner is the printable equivalent: it
// braces the whole transition, costs nothing extra in the extrusion, and
// doubles as a lead-in ramp for the toe.
// =====================================

$fn = 64;

// ---- Parameters (mm) ----
base_run  = 15;    // base run from the panel's back face; keep <= actual panel thickness
rear_t    = 4;     // fixing plate thickness — all that stands proud inside the drawer
rear_h    = 60;    // how far the fixing plate rises up the inside face
base_t    = 5;     // thickness of the piece under the panel's bottom edge
lip_t     = 4;     // toe lip thickness
lip_h     = 16;    // how far the toe lip juts down below the base
web_drop  = 5;     // corner web depth down the lip's back face (0 = no web)
width     = 120;   // bracket width along the panel; also the printed height
screw_holes = true; // false = no drilling, bond the plate on with VHB tape

// ---- Fixed (not exposed in the customizer) ----
screw_d = 4.4;      // screw shank clearance diameter
screw_head_d = 8.4; // screw head diameter
csk_depth = 2.0;    // countersink depth
screw_edge = 9;
screw_y_lo = 20;
screw_y_hi = 50;

// ---- Derived ----
x0 = -rear_t;              // fixing plate outer face
x1 = 0;                     // panel back face
x2 = base_run - lip_t;      // lip back face — the surface the toe catches
x3 = base_run;              // front edge of the recessed base run
yb = -base_t;               // base underside
yl = -base_t - lip_h;       // lip bottom

// Clamped, not asserted: on a thin panel the web is shallower than 2 *
// web_drop implies, which is intended — don't turn this into an assert.
web_run = (web_drop > 0) ? min(2 * web_drop, base_run - lip_t - 2) : 0;
screw_sp  = width * 0.6;

assert(rear_t >= csk_depth + 1.5, "rear_t too thin for the screw countersink");
assert(lip_h - web_drop >= 6, "web_drop leaves too little lip for a toe to catch");
assert(base_run - lip_t - 2 > 0, "lip_t too thick for this base_run");
assert(rear_h - screw_y_hi >= screw_head_d / 2 + 2, "rear_h too short for the top screw row");
assert(screw_y_lo - screw_head_d / 2 >= 1.5, "lower screw row would break into the base");
assert(screw_y_hi - screw_y_lo >= screw_head_d + 2, "screw rows too close together");
assert((width - screw_sp) / 2 >= screw_head_d / 2 + 3, "screws too close to the ends");
assert(base_t >= 3, "base_t too thin to carry a foot load");

module profile() {
    polygon(points = [
        [x0, rear_h],
        [x1, rear_h],
        [x1, 0],
        [x3, 0],
        [x3, yl],
        [x2, yl],
        [x2, yb - web_drop],
        [x2 - web_run, yb],
        [x0, yb],
    ]);
}

module screw_cuts() {
    for (cy = [screw_y_lo, screw_y_hi]) {
        for (s = [-1, 1]) {
            let (cz = width / 2 + s * screw_sp / 2) {
                // Shank
                translate([x0 - 1, cy, cz])
                    rotate([0, 90, 0])
                        cylinder(d = screw_d, h = rear_t + 2);
                // Countersink — must open on the x0 face (the exposed face inside
                // the drawer) so the head sits flush and cannot foul the bin.
                // Opening it on x1 would put the heads inside the panel. The 0.02
                // overshoot avoids a coplanar cut face.
                translate([x0 - 0.02, cy, cz])
                    rotate([0, 90, 0])
                        cylinder(d1 = screw_head_d, d2 = screw_d, h = csk_depth);
            }
        }
    }
}

module bin_foot_pull() {
    difference() {
        linear_extrude(height = width, convexity = 4)
            profile();
        if (screw_holes)
            screw_cuts();
    }
}

bin_foot_pull();
