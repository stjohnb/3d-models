// =====================================
// Sink Tray Foot
// Cylindrical foot attached to tray by a screw
// =====================================

$fn = 64;

// ---- Parameters (mm) ----
total_height = 25;

r0 = 2;     // screw shaft hole radius
r1 = 4;     // counterbore radius (screw head clearance)
r2 = 6;     // outer radius

top_bore = 15;    // counterbore depth from top
bottom_bore = 5;  // counterbore depth from bottom
// middle section = total_height - top_bore - bottom_bore = 5mm (solid ring at r0)

// ---- Assembly ----
difference() {
    // Solid cylinder
    cylinder(r = r2, h = total_height);

    // Counterbore from top (for screw head)
    translate([0, 0, total_height - top_bore])
        cylinder(r = r1, h = top_bore + 0.1);

    // Counterbore from bottom
    translate([0, 0, -0.1])
        cylinder(r = r1, h = bottom_bore + 0.1);

    // Narrow screw shaft hole through the middle section
    translate([0, 0, bottom_bore])
        cylinder(r = r0, h = total_height - top_bore - bottom_bore);
}
