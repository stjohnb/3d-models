// =====================================
// Resistor storage box
// Open-top box that files resistor-kit bags on edge like index cards,
// plus a push-on lid. Sized to the issue's 10 x 7 x 7 cm outer envelope.
// =====================================
// Parts:
//   resistor_box     -> resistor_box.stl      (open-top box with end-wall thumb scoops)
//   resistor_box_lid -> resistor_box_lid.stl  (flat lid with an inner locating lip)
//
// Orientation: Z-up, centred on X/Y, base at z=0. The box prints floor-down
// as exported. The lid is modelled top-face-down (plate on the bed, lip
// rising from it) so it also prints flat without supports.
//
// Bag assumption: 1/4 W kit bags (~100 mm x 65 mm, ~2.5-3 mm thick with 20
// taped resistors) stand on their 100 mm edge along X and file across Y,
// so a 25-value kit fills the ~67 mm cavity width. The two end walls carry a
// U-shaped thumb scoop so a single bag's end can be pinched and lifted out,
// and so a thumb can push the fitted lid up from below.

$fn = 64;

// ---- Outer envelope (mm) ----
outer_l = 100;   // X: the bags' long edge lies along this
outer_w = 70;    // Y: bags file across this
outer_h = 70;    // Z: open-top box height, lid adds lid_t on top

// ---- Walls ----
wall     = 1.6;  // side wall thickness (4 perimeters at 0.4 mm)
floor_t  = 1.6;  // floor thickness
corner_r = 4;    // outer vertical corner radius

// ---- Thumb scoops in the two end (Y-Z) walls ----
scoops      = true;
scoop_w     = 26;  // scoop width across the end wall
scoop_depth = 22;  // scoop depth below the rim (>= scoop_w/2 for the round bottom)

// ---- Lid ----
lid_t         = 2;    // lid plate thickness
lip_h         = 5;    // how far the locating lip drops into the cavity
lip_t         = 1.6;  // lip wall thickness
lid_clearance = 0.3;  // per-side gap between the lip and the cavity wall

// ---- Derived ----
inner_l  = outer_l - 2 * wall;
inner_w  = outer_w - 2 * wall;
inner_r  = max(corner_r - wall, 0.5);
cavity_h = outer_h - floor_t;
lip_l    = inner_l - 2 * lid_clearance;
lip_w    = inner_w - 2 * lid_clearance;
lip_r    = max(inner_r - lid_clearance, 0.5);
// Clamp rather than assert on the raw customizer values: scoop_w and
// scoop_depth are bounded by outer_w/corner_r and cavity_h respectively, and
// those bounds shift independently of scoop_w/scoop_depth's own manifest
// ranges, so a hard assert can reject combinations that are each in-range.
eff_scoop_w     = min(scoop_w, outer_w - 2 * corner_r - 2);
eff_scoop_depth = min(scoop_depth, cavity_h - 10);
scoop_z0 = outer_h - eff_scoop_depth + eff_scoop_w / 2;  // centre of the scoop's round bottom

assert(!scoops || eff_scoop_depth >= eff_scoop_w / 2,
       "scoop_depth must be at least scoop_w/2 for the rounded bottom");
assert(lip_l > 2 * lip_t + 10 && lip_w > 2 * lip_t + 10,
       "box too small for the lid lip");

// Rounded-rectangle vertical prism: hull of four corner cylinders.
// l along X, w along Y, centred on X/Y, base at z=0.
module rbox(l, w, h, r) {
    hull()
        for (sx = [-1, 1], sy = [-1, 1])
            translate([sx * (l / 2 - r), sy * (w / 2 - r), 0])
                cylinder(r = r, h = h);
}

// U-shaped cutter for one end wall: a horizontal cylinder along X for the
// round bottom plus a block up past the rim. Centred on X/Y; the caller
// translates it onto the wall. Cuts wall + 2 mm along X.
module scoop_cutter() {
    translate([0, 0, scoop_z0])
        rotate([0, 90, 0])
            cylinder(d = eff_scoop_w, h = wall + 2, center = true);
    translate([-(wall + 2) / 2, -eff_scoop_w / 2, scoop_z0])
        cube([wall + 2, eff_scoop_w, outer_h - scoop_z0 + 1]);
}

// Open-top box, floor on the bed.
module resistor_box() {
    difference() {
        rbox(outer_l, outer_w, outer_h, corner_r);
        translate([0, 0, floor_t])
            rbox(inner_l, inner_w, cavity_h + 1, inner_r);
        if (scoops)
            for (sx = [-1, 1])
                translate([sx * (outer_l / 2 - wall / 2), 0, 0])
                    scoop_cutter();
    }
}

// Lid, modelled top-face-down: the plate sits on the bed and the lip
// rises from it; flip it over to fit the box.
module resistor_box_lid() {
    rbox(outer_l, outer_w, lid_t, corner_r);
    translate([0, 0, lid_t - 0.01])
        difference() {
            rbox(lip_l, lip_w, lip_h + 0.01, lip_r);
            translate([0, 0, -1])
                rbox(lip_l - 2 * lip_t, lip_w - 2 * lip_t, lip_h + 3,
                     max(lip_r - lip_t, 0.5));
        }
}
