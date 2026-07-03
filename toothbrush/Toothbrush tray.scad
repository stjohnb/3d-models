// =====================================
// Fully Rounded Drip Tray with Alignment Grooves
// Tray: 100 x 50 x 10 mm, sits on holder base via alignment notches
// =====================================

include <_toothbrush_holder.scad>

// ---- Tray Dimensions (mm) ----
tray_length = 100;
tray_width  = 50;
tray_height = 10;

wall_thickness   = 2;
bottom_thickness = 2;

outer_corner_radius = 8;

inner_corner_radius = outer_corner_radius - wall_thickness;
inner_bottom_radius = 1.5;   // internal bottom fillet

// ---- Alignment Groove Parameters ----
groove_clearance = 0.2;        // clearance per side around peg
groove_length    = peg_length + 2 * groove_clearance;
groove_width     = peg_width  + 2 * groove_clearance;
groove_depth     = 4;          // deeper than peg for easy entry
groove_spacing_x = grip_spacing / 2;

$fn = 64;


// ---- 2D Rounded Rectangle ----
module rounded_rect_2d(length, width, radius) {
    offset(r = radius)
        square([length - 2*radius, width - 2*radius], center = true);
}


// ---- Outer Shell ----
module outer_shell() {
    minkowski() {
        linear_extrude(tray_height - outer_bottom_radius)
            rounded_rect_2d(tray_length, tray_width, outer_corner_radius);

        sphere(r = outer_bottom_radius);
    }
}


// ---- Inner Cavity (Rounded) ----
module inner_cavity() {

    translate([0, 0, bottom_thickness + inner_bottom_radius])
        minkowski() {
            linear_extrude(tray_height)
                rounded_rect_2d(
                    tray_length - 2*wall_thickness,
                    tray_width  - 2*wall_thickness,
                    max(inner_corner_radius, 0)
                );

            sphere(r = inner_bottom_radius);
        }
}


// ---- Final Tray with Alignment Grooves ----
module drip_tray() {
    difference() {
        // Tray shell
        difference() {
            outer_shell();
            inner_cavity();
        }

        // Alignment grooves recessed into bottom, centered on tray
        for (xoff = [-groove_spacing_x, groove_spacing_x])
            translate([xoff, 0, -outer_bottom_radius - 0.01])
                cube([groove_length, groove_width, groove_depth], center = true);
    }
}

// ---- Assembly ----
drip_tray();
