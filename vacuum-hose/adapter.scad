// =====================================
// Vacuum Hose Adapter
// 50mm OD spigot end → 35mm OD spigot end (both ends male)
// Total length 100mm, 2mm walls
// =====================================

$fn = 64;

// ---- Parameters (mm) ----
total_length = 100;
tip_length   = 10;  // taper zone at each end

wall = 2;

// Z breakpoints
z_large_tip  = 0;
z_large_body = tip_length;
z_small_body = total_length - tip_length;
z_small_tip  = total_length;

// Outer diameters at each Z breakpoint
od_large_body = 50;
od_small_body = 35;
od_large_tip  = od_large_body - 2;  // 2mm narrower than body to aid insertion
od_small_tip  = od_small_body - 2;  // 2mm narrower than body to aid insertion

// Inner diameters (2mm wall on each side → -4mm)
id_large_tip  = od_large_tip  - 2*wall;
id_large_body = od_large_body - 2*wall;
id_small_body = od_small_body - 2*wall;
id_small_tip  = od_small_tip  - 2*wall;

// ---- Helpers ----
module disc(d, h = 0.01) {
    cylinder(d = d, h = h);
}

module taper_segment(d1, d2, z1, z2) {
    hull() {
        translate([0, 0, z1]) disc(d1);
        translate([0, 0, z2]) disc(d2);
    }
}

// ---- Outer shell ----
module outer_shell() {
    taper_segment(od_large_tip,  od_large_body, z_large_tip,  z_large_body);
    taper_segment(od_large_body, od_small_body, z_large_body, z_small_body);
    taper_segment(od_small_body, od_small_tip,  z_small_body, z_small_tip);
}

// ---- Inner bore ----
module inner_bore() {
    taper_segment(id_large_tip,  id_large_body, z_large_tip,  z_large_body);
    taper_segment(id_large_body, id_small_body, z_large_body, z_small_body);
    taper_segment(id_small_body, id_small_tip,  z_small_body, z_small_tip + 0.2);
}

// ---- Assembly ----
rotate([-90, 0, 0])
difference() {
    outer_shell();
    translate([0, 0, -0.1]) inner_bore();
}
