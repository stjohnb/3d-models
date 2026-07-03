// =====================================
// Vacuum Hose Reducer
// 49mm ID socket end → spigot end (fits 30mm ID hose)
// Total length ~100mm, 2mm walls
// =====================================

$fn = 64;

// ---- Parameters (mm) ----
total_length = 100;

wall = 2;

// Z breakpoints
z_large_end  = 0;
z_large_body = 20;
z_small_body = 40;
z_small_end  = total_length;  // 100

// Outer diameters at each Z breakpoint
// Z=0:   OD=55, ID=51  (2mm wall, flared tip)
// Z=20:  OD=53, ID=49  (2mm wall, socket bore)
// Z=40:  OD=34, ID=30  (2mm wall, transition end)
// Z=100: OD=28, ID=24  (2mm wall, spigot tip)

od_large_tip  = od_large_body + 2;  // bell-mouth: 2mm wider than body to aid hose seating
od_large_body = 53;
od_small_body = 34;
od_small_tip  = od_small_body - 6;  // spigot tip: 6mm narrower than body

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
    union() {
        taper_segment(od_large_tip,  od_large_body, z_large_end,  z_large_body);
        taper_segment(od_large_body, od_small_body, z_large_body, z_small_body);
        taper_segment(od_small_body, od_small_tip,  z_small_body, z_small_end);
    }
}

// ---- Inner bore ----
module inner_bore() {
    union() {
        taper_segment(id_large_tip,  id_large_body, z_large_end,  z_large_body);
        taper_segment(id_large_body, id_small_body, z_large_body, z_small_body);
        taper_segment(id_small_body, id_small_tip,  z_small_body, z_small_end + 0.1);
    }
}

// ---- Assembly ----
rotate([-90, 0, 0])
difference() {
    outer_shell();
    translate([0, 0, -0.1]) inner_bore();
}
