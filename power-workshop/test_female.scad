// =====================================
// Test print - Female connection (socket in a short cylinder)
// Quick print to verify fit against male shaft
// =====================================

include <_connection.scad>

$fn = 64;

// Minimal surrounding wall
wall = 3;
body_diameter = socket_size * 1.42 + wall * 2;  // enough to enclose the square socket
// Height equals shaft length so the collar face sits flush on the top when assembled.
// This also ensures both STLs are in their assembled position at z=0 for interference
// checking: shaft tip (z=0) aligns with socket floor, collar (z=shaft_sq_length) rests
// on the top face of this body.
body_height = shaft_sq_length;

// ---- Assembly: short cylinder with socket opening at the top ----
difference() {
    cylinder(d = body_diameter, h = body_height);

    // Socket opens at the top (z=body_height).  Rotate 180° so the square_socket
    // module's opening (local z=0) faces upward, then translate to the top face.
    translate([0, 0, body_height])
        rotate([180, 0, 0])
            square_socket();
}
