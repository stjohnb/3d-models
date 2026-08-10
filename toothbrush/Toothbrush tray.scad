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

// ---- Head Spike Parameters (mm) ----
spike_height  = 20;   // total height above the tray floor, including the domed tip
spike_base_d  = 4;    // diameter where the spike meets the floor
spike_tip_d   = 3;    // diameter at the tip
spike_flare   = 1.5;  // beveled flare at the base for strength
spike_spacing = 30;   // centre-to-centre X spacing
spike_y       = 15;   // Y offset — forward of the alignment grooves at y = 0

// ---- Brush Support Spike Parameters (mm) ----
// Two extra spikes directly under the toothbrush clips, so a parked brush
// rests on a point instead of standing in water on the tray floor (issue #374).
// X matches the clip centres exactly — same value the alignment grooves use.
// Y is pulled back from the clip bore axis (tray-local y = -3.5) just far
// enough that the flared base clears the alignment groove footprint, keeping
// the ~1.5mm of floor above a groove free of any post, as the head spikes do.
brush_spike_spacing = grip_spacing;   // 40 — clip centre-to-centre
brush_spike_y       = -(groove_width / 2 + spike_base_d / 2 + spike_flare + 0.5);  // -6.2

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


// ---- Vertical spike for parking a detached brush head (issue #371) ----
// Origin at the tray's inner floor plane; base is sunk 0.5mm into the floor so
// the union is unambiguous rather than coplanar.
module head_spike() {
    hull() {
        translate([0, 0, -0.5])
            cylinder(d = spike_base_d + 2 * spike_flare, h = 0.01);
        translate([0, 0, spike_flare])
            cylinder(d = spike_base_d, h = 0.01);
    }
    cylinder(d1 = spike_base_d, d2 = spike_tip_d, h = spike_height - spike_tip_d / 2);
    translate([0, 0, spike_height - spike_tip_d / 2])
        sphere(d = spike_tip_d);
}

// ---- Final Tray with Alignment Grooves ----
module drip_tray() {
    union() {
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

        // Brush-head parking spikes, rising from the inner floor
        for (xoff = [-spike_spacing / 2, spike_spacing / 2])
            translate([xoff, spike_y, bottom_thickness])
                head_spike();

        // Brush support spikes, directly under each toothbrush clip (issue #374)
        for (xoff = [-brush_spike_spacing / 2, brush_spike_spacing / 2])
            translate([xoff, brush_spike_y, bottom_thickness])
                head_spike();
    }
}

// ---- Assembly ----
drip_tray();
