// =====================================
// Fisher-Price Power Workshop - Drill Bit Attachment
// Plugs into power handle
// Toy drill bit with shallow spiral flutes and cog teeth
// on top to mesh with workbench gear
// =====================================

// ---- Parameters (mm) ----
$fn = 64;
include <_connection.scad>

// Drill body
drill_diameter = 21;     // main drill shaft diameter
drill_length = 60;       // length of fluted section

// Spiral flutes - very lightly engraved surface lines
num_flutes = 2;          // number of spiral channels
flute_depth = 0.3;       // barely recessed, no more than 2mm from edge
flute_width = 1.0;       // thin groove
flute_twist = -720;      // 2 full rotations over drill_length (right-hand helix)

// Cog teeth on top (meshes with workbench gear)
cog_height = 5;          // height of cog section
num_teeth = 20;          // number of rounded gear teeth
tooth_depth = 2;         // how deep the tooth valleys cut

// ---- Modules ----

// Tooth cross-section: rectangle with quarter-round on outer-top corner.
// Used for cog teeth that mesh with the workbench gear.
module tooth_profile(w, h, r) {
    polygon(concat(
        [[0, 0], [w, 0], [w, h - r]],
        [for (a = [0:5:90]) [w - r + r * cos(a), h - r + r * sin(a)]],
        [[0, h]]
    ));
}

// Shallow flute channel profile
module flute_profile() {
    translate([drill_diameter/2 - flute_depth/2, 0, 0])
        circle(d = flute_width);
}

// Main drill body with shallow spiral flutes
module drill_body() {
    body_start = shaft_sq_length + collar_length;

    translate([0, 0, body_start])
    difference() {
        cylinder(d = drill_diameter, h = drill_length);

        // Shallow spiral flute channels
        for (i = [0:num_flutes-1]) {
            rotate([0, 0, i * 360 / num_flutes])
            linear_extrude(drill_length, twist = flute_twist)
                flute_profile();
        }
    }
}

// Cog teeth on top - quarter-round on outer edge of each tooth
module cog_top() {
    cog_start = shaft_sq_length + collar_length + drill_length;
    cog_outer_r = drill_diameter / 2;
    cog_inner_r = cog_outer_r - tooth_depth;
    round_r = 1.0;  // quarter-round radius on outer top edge
    tooth_width = 3.14159 * cog_inner_r / num_teeth;

    translate([0, 0, cog_start]) {
        // Inner hub
        cylinder(r = cog_inner_r, h = cog_height);

        // Teeth with quarter-round on outer top edge
        for (i = [0:num_teeth-1]) {
            rotate([0, 0, i * 360 / num_teeth])
            translate([cog_inner_r, 0, 0])
            rotate([90, 0, 0])
                linear_extrude(tooth_width, center = true)
                    tooth_profile(tooth_depth, cog_height, round_r);
        }
    }
}

// ---- Assembly ----
union() {
    sq_shaft();
    collar();
    drill_body();
    cog_top();
}
