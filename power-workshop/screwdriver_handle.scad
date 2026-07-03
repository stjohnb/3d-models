// =====================================
// Fisher-Price Power Workshop - Screwdriver Handle
// Manual handle for screwdriver/wrench attachments
// =====================================

include <_connection.scad>

// ---- Parameters (mm) ----
$fn = 64;

// Handle dimensions
handle_length = 95;     // total length
grip_diameter = 34;     // widest part of barrel grip
handle_collar_d = 22;   // collar around the socket opening
handle_collar_len = 15; // length of collar at bottom

// Grip texture
num_ridges = 12;            // longitudinal ridges on grip
grip_groove_depth = 1.2;    // depth of grooves between ridges
grip_groove_width = 2;      // width of each groove

// ---- Modules ----

// Barrel-shaped grip built from stacked hull slices for a smooth profile
// Profile: collar -> taper out -> barrel -> dome top
module handle_body() {
    // Collar at the bottom
    cylinder(d = handle_collar_d, h = handle_collar_len);

    // Taper from collar to grip
    translate([0, 0, handle_collar_len])
    hull() {
        cylinder(d = handle_collar_d, h = 0.1);
        translate([0, 0, 12])
            cylinder(d = grip_diameter, h = 0.1);
    }

    // Main barrel section
    translate([0, 0, handle_collar_len + 12])
        cylinder(d = grip_diameter, h = 40);

    // Taper from barrel to top dome
    translate([0, 0, handle_collar_len + 12 + 40])
    hull() {
        cylinder(d = grip_diameter, h = 0.1);
        translate([0, 0, 10])
            cylinder(d = grip_diameter - 6, h = 0.1);
    }

    // Rounded dome top
    translate([0, 0, handle_collar_len + 12 + 40 + 10])
    scale([1, 1, 0.6])
        sphere(d = grip_diameter - 6);
}

// Grip ridges (subtractive grooves along the barrel)
module grip_grooves() {
    groove_start = handle_collar_len + 8;
    groove_length = 50;
    for (i = [0:num_ridges-1]) {
        angle = i * 360 / num_ridges;
        rotate([0, 0, angle])
        translate([grip_diameter/2 - grip_groove_depth/2, 0, groove_start])
            cylinder(d = grip_groove_width, h = groove_length);
    }
}

// ---- Assembly ----
difference() {
    handle_body();
    square_socket();
    grip_grooves();
}
