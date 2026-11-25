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
//
// The fixing plate is relieved over its bottom relief_h mm, where the drawer
// face meets the front edge of the cabinet's bottom panel. That band is the
// only part of the bracket that holds the drawer front proud when closed, so
// it is thinned to relief_t; above it the plate returns to rear_t for
// stiffness and screw purchase. The screws are deliberately NOT countersunk:
// their heads sit on the plate face above the relief band, where nothing in
// the cabinet backs onto them.
// =====================================

$fn = 64;

// ---- Parameters (mm) ----
base_run  = 15;    // base run from the panel's back face; keep <= actual panel thickness
rear_t    = 4;     // fixing plate thickness above the relief band
relief_h  = 22;    // bottom band of the plate that meets the cabinet's bottom
                   // panel; measured up from the panel's bottom edge (0 = none)
relief_t  = 1.6;   // plate thickness inside that band — this is all that holds
                   // the drawer front proud when closed
rear_h    = 60;    // how far the fixing plate rises up the inside face
base_t    = 5;     // thickness of the piece under the panel's bottom edge
lip_t     = 4;     // toe lip thickness
lip_h     = 16;    // how far the toe lip juts down below the base
web_drop  = 5;     // corner web depth down the lip's back face (0 = no web)
width     = 120;   // bracket width along the panel; also the printed height
screw_holes = true; // false = no drilling, bond the plate on with VHB tape

// ---- Fixed (not exposed in the customizer) ----
screw_d = 4.4;      // screw shank clearance diameter
screw_head_d = 8.4; // head diameter — bears on the plate face, no countersink
screw_edge = 9;

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

xr = -relief_t;                                              // relieved outer face
relief_top = (relief_h > 0) ? relief_h + rear_t - relief_t : 0;  // top of the 45deg ramp

// Screw rows are derived, not fixed: both must land in the full-thickness
// plate above the relief ramp, and clear the top edge.
screw_y_lo = max(relief_top + screw_head_d / 2 + 3, 20);
screw_y_hi = rear_h - screw_head_d / 2 - 4;

back_face = (relief_h > 0)
    ? [[xr, 0], [xr, relief_h], [x0, relief_top]]
    : [];

assert(rear_t >= 3, "rear_t too thin to hold a screw");
assert(relief_t >= 1.2, "relief_t too thin to print as solid perimeters");
assert(rear_t - relief_t >= 1, "relief_t must be at least 1mm thinner than rear_t");
assert(lip_h - web_drop >= 6, "web_drop leaves too little lip for a toe to catch");
assert(base_run - lip_t - 2 > 0, "lip_t too thick for this base_run");
assert(rear_h - screw_y_hi >= screw_head_d / 2 + 2, "rear_h too short for the top screw row");
assert(screw_y_lo - screw_head_d / 2 >= relief_top + 1.5, "lower screw row would overhang the relief ramp");
assert(screw_y_hi - screw_y_lo >= screw_head_d + 2, "screw rows too close together");
assert((width - screw_sp) / 2 >= screw_head_d / 2 + 3, "screws too close to the ends");
assert(base_t >= 3, "base_t too thin to carry a foot load");

module profile() {
    polygon(points = concat([
        [x0, rear_h],
        [x1, rear_h],
        [x1, 0],
        [x3, 0],
        [x3, yl],
        [x2, yl],
        [x2, yb - web_drop],
        [x2 - web_run, yb],
        [x0, yb],
    ], back_face));
}

module screw_cuts() {
    for (cy = [screw_y_lo, screw_y_hi]) {
        for (s = [-1, 1]) {
            let (cz = width / 2 + s * screw_sp / 2) {
                // Shank only. The heads are not countersunk: they sit proud on
                // the x0 face above the relief band, where no cabinet material
                // backs onto them.
                translate([x0 - 1, cy, cz])
                    rotate([0, 90, 0])
                        cylinder(d = screw_d, h = rear_t + 2);
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
