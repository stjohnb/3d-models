// =====================================
// Fully Rounded Drip Tray with Alignment Grooves
// Tray: 100 x 65 x 10 mm, sits on holder base via alignment notches; front edge overhangs the base by 15mm (issue #377)
// =====================================

include <_toothbrush_holder.scad>

// ---- Tray Dimensions (mm) ----
tray_length = 100;
tray_width  = 65;   // front-to-back; grown forward only (issue #377)
tray_height = 10;

wall_thickness   = 2;
bottom_thickness = 2;

// The tray grows forward only (issue #377): the base and its alignment pegs
// are already printed, so the tray's local origin stays on the peg line at
// world y = peg_y and only the shell is offset forward.
tray_back_gap = 5;                                       // backplate plane to tray back edge
tray_shift_y  = tray_back_gap + tray_width / 2 - peg_y;  // 7.5

outer_corner_radius = 8;

inner_corner_radius = outer_corner_radius - wall_thickness;
inner_bottom_radius = 1.5;   // internal bottom fillet

// ---- Alignment Groove Parameters ----
groove_clearance = 0.2;        // clearance per side around peg
groove_length    = peg_length + 2 * groove_clearance;
groove_width     = peg_width  + 2 * groove_clearance;
groove_depth     = 4;          // deeper than peg for easy entry
groove_spacing_x = grip_spacing / 2;

// ---- Head Peg Parameters (mm) ----
// Posts for parking detached brush heads (issue #371). Enlarged to an 8mm
// shaft tapering to a flat, rounded tip, and moved to the tray's front
// corners so a parked head can't clash with the brushes hanging in the
// clips (issue #388).
head_peg_d       = 8;     // shaft diameter
head_peg_height  = 30;    // total height above the tray floor
head_peg_taper   = 10;    // top section, tapering from head_peg_d to head_peg_tip_d
head_peg_tip_d   = 6;     // flat tip diameter (3mm radius, PR #389 review)
head_peg_flare   = 1.5;   // beveled flare where the shaft meets the floor
head_peg_gap     = 1;     // clearance from the flared base to the cavity corner
head_peg_outer_r = head_peg_d / 2 + head_peg_flare;   // 5.5 — flare radius
head_r           = 11;    // external radius of a parked toothbrush head at its
                           // base — larger than the peg itself, so it's the
                           // controlling clearance to the tray wall (PR #389 review)

// Front corners of the inner cavity, inset by head_r (the parked head's own
// radius, not just the peg's flare) plus head_peg_gap so the head clears the
// corner fillet and side walls.
head_peg_x = tray_length / 2 - wall_thickness - head_r - head_peg_gap;  // 36
head_peg_y = tray_shift_y + tray_width / 2
             - wall_thickness - head_r - head_peg_gap;                  // 26

// ---- Brush Support Spike Parameters (mm) ----
// Two spikes directly under the toothbrush clips, so a parked brush rests on a
// point instead of standing in water on the tray floor (issue #374).
// X matches the clip centres exactly — same value the alignment grooves use.
// Y is pulled back from the clip bore axis (tray-local y = -3.5) just far
// enough that the flared base clears the alignment groove footprint.
spike_height  = 30;   // 10mm taller than the original 20mm (issue #388)
spike_base_d  = 4;
spike_tip_d   = 3;
spike_flare   = 1.5;
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


// ---- Corner peg for parking a detached brush head (issues #371, #388) ----
// Origin at the tray's inner floor plane; base sunk 0.5mm into the floor so the
// union is unambiguous rather than coplanar. Straight 8mm shaft for the lower
// 20mm, then a cone tapering to a flat 3mm-radius tip over the top 10mm.
module head_peg() {
    hull() {
        translate([0, 0, -0.5])
            cylinder(d = head_peg_d + 2 * head_peg_flare, h = 0.01);
        translate([0, 0, head_peg_flare])
            cylinder(d = head_peg_d, h = 0.01);
    }
    cylinder(d = head_peg_d, h = head_peg_height - head_peg_taper);
    translate([0, 0, head_peg_height - head_peg_taper])
        cylinder(d1 = head_peg_d, d2 = head_peg_tip_d, h = head_peg_taper);
}

// ---- Support spike under each clip (issue #374) ----
// Origin at the tray's inner floor plane; base sunk 0.5mm into the floor.
module support_spike() {
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
            // Tray shell, offset forward from the peg line
            translate([0, tray_shift_y, 0])
            difference() {
                outer_shell();
                inner_cavity();
            }

            // Alignment grooves recessed into bottom, on the peg line
            for (xoff = [-groove_spacing_x, groove_spacing_x])
                translate([xoff, 0, -outer_bottom_radius - 0.01])
                    cube([groove_length, groove_width, groove_depth], center = true);
        }

        // Brush-head parking pegs, at the tray's front corners (issue #388)
        for (xoff = [-head_peg_x, head_peg_x])
            translate([xoff, head_peg_y, bottom_thickness])
                head_peg();

        // Brush support spikes, directly under each toothbrush clip (issue #374)
        for (xoff = [-brush_spike_spacing / 2, brush_spike_spacing / 2])
            translate([xoff, brush_spike_y, bottom_thickness])
                support_spike();
    }
}

// ---- Assembly ----
drip_tray();
