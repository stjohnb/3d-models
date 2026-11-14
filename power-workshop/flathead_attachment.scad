// =====================================
// Fisher-Price Power Workshop - Flathead Screwdriver Attachment
// Plugs into power handle or screwdriver handle
// =====================================

// ---- Parameters (mm) ----
$fn = 64;
include <_connection.scad>

// Shaft between square peg and blade
shaft_diameter = 12;
shaft_length = 30;       // visible shaft length

// Flathead blade
blade_width = 15;       // width of the flat blade
blade_thickness = 3.5;  // thickness of flat blade
blade_length = 15;      // how far the blade extends
blade_taper = 8;        // length of taper from shaft to blade

// Total length approx: hex_length + collar_length + shaft_length + blade_taper + blade_length

// ---- Modules ----

// Round shaft
module shaft() {
    translate([0, 0, shaft_sq_length + collar_length])
        cylinder(d = shaft_diameter, h = shaft_length);
}

// Flathead blade with taper
module flathead_blade() {
    tip_start = shaft_sq_length + collar_length + shaft_length;

    // Taper from round shaft to flat blade
    translate([0, 0, tip_start])
    hull() {
        // Base matches shaft
        cylinder(d = shaft_diameter, h = 0.1);
        // Tip is flat
        translate([0, 0, blade_taper])
            cube([blade_width, blade_thickness, 0.1], center = true);
    }

    // Flat blade extension
    translate([0, 0, tip_start + blade_taper])
    hull() {
        cube([blade_width, blade_thickness, 0.1], center = true);
        // Slight taper at very tip
        translate([0, 0, blade_length])
            cube([blade_width - 2, blade_thickness - 0.5, 0.1], center = true);
    }
}

// ---- Assembly ----
union() {
    sq_shaft();
    collar();
    shaft();
    flathead_blade();
}
