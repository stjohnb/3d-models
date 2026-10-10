// =====================================
// Fisher-Price Power Workshop - Drill Socket
// Adapter for the drill press: transfers rotation from power
// handle (male shaft at bottom) through a 90-degree bevel gear
// (at top) into the drill press mechanism. A female square
// socket inside the top accepts the drill bit's male shaft.
// See DRILL_SOCKET_SPEC.md for measurement details
// =====================================

// ---- Parameters (mm) ----
$fn = 64;
include <_connection.scad>

// Override socket depth for drill-socket-specific deeper bore.
// Standard is 13mm; drill socket needs 21mm to fully accept
// the drill bit shaft. OpenSCAD "last assignment wins" semantics
// make this override work for square_socket().
socket_depth = 21;

// Override ridge_pos so the snap ridge lands in the body+boss region,
// below the 13mm nose bore that would otherwise erase it. The standard
// 7.35mm depth falls inside the nose bore subtraction (z ≈ 36.6–39.7),
// which deletes the ridge entirely. At 15.35mm the ridge sits at
// z ≈ 29.2–32.3, inside the solid boss/body material, and aligns with
// the drill bit's groove when the bit is fully seated.
ridge_pos = 15.35;

// Drill-socket-specific male connection overrides.
// The drill socket male end is smaller than the standard attachment
// connection (which is 8.2mm shaft, 12.5mm collar).
shaft_sq = 6.5;            // side length (standard is 8.2mm)
collar_diameter = 9.5;     // collar OD (standard is 12.5mm)

// Nose (smooth cylindrical tip at top)
nose_d = 16;               // external diameter (caliper-measured)
nose_inner_d = 13;         // internal bore diameter
nose_h = 8;

// Bevel gear teeth
teeth_h = 8;
num_bevel_teeth = 24;
tooth_depth = 1.5;  // valleys recessed from body OD (12.75 - 1.5 = 11.25mm radius = 22.5mm valley diameter)

// Body (hollow with 2mm walls)
body_d = 25.5;
body_h = 8;
body_wall = 2;
body_inner_d = body_d - 2 * body_wall;  // hollow interior diameter (21.5mm)

// Socket boss — narrower than body_inner_d to preserve ring cavity in body interior.
// Square socket diagonal ≈ 12.16mm; 16mm gives ~2mm walls at the corners.
socket_boss_d = 16;

// Gap between flange top and socket boss start — 2mm stand-off
// leaves a ring cavity at the base of the body for the drill to seat into.
socket_boss_gap = 2;

// Flange (mechanical stop — max diameter)
flange_d = 28.5;
flange_h = 2;

// Drill-socket-specific male connection lengths
// (standard collar is 8.3mm, standard shaft is 12.4mm)
ds_collar_h = 12;
ds_shaft_h = 6.5;

// Bottom cylindrical piece
cyl_d = 6;
cyl_h = 1;

// Internal bore
bore_d = 4;
bore_extra = 1.5;  // Extension of internal bore beyond flange base within the flange

// ---- Z-axis layout ----
// Building from bottom (z=0):
//   0      -> 1      : cylindrical piece (1mm, 6mm OD, 4mm bore through centre)
//   1      -> 7.5    : square shaft (6.5mm, 6.5mm sides)
//   7.5    -> 19.5   : collar (12mm visible, 9.5mm OD; continues internally to z=29.5)
//   19.5   -> 21.5   : flange (2mm)
//   21.5   -> 23.5   : ring cavity (2mm, full body ID — boss stand-off from flange)
//   23.5   -> 29.5   : socket boss (6mm, 16mm OD)
//   21.5   -> 29.5   : body shell (8mm, hollow 2mm walls)
//   29.5   -> 37.5   : bevel teeth (8mm, tips flush with body/nose OD)
//   37.5   -> 45.5   : nose (8mm, 16mm OD, 13mm ID bore)
total_height = cyl_h + ds_shaft_h + ds_collar_h + flange_h + body_h + teeth_h + nose_h;

z_shaft   = cyl_h;
z_collar  = z_shaft + ds_shaft_h;
z_flange  = z_collar + ds_collar_h;
z_body    = z_flange + flange_h;
z_teeth   = z_body + body_h;
z_nose    = z_teeth + teeth_h;

// ---- Modules ----

// Bottom cylindrical piece (1mm tall, 6mm diameter, 4mm bore through centre)
module ds_bottom_cylinder() {
    cylinder(d = cyl_d, h = cyl_h);
}

// Custom male square shaft — 6.5mm long, no snap groove.
// The shaft is too short for the standard groove (which extends to
// 6.6mm). The drill socket retains position mechanically in the
// drill press housing, not via snap-fit.
module ds_shaft() {
    translate([0, 0, z_shaft])
        linear_extrude(ds_shaft_h)
            _shaft_profile(shaft_sq);
}

// Custom collar — 12mm external height (standard is 8.3mm); extends internally
// as a cylinder through the flange and body to z_teeth (z=29.5mm).
// Same hull technique as collar() in _connection.scad.
module ds_collar() {
    translate([0, 0, z_collar]) {
        // Taper from square shaft to round collar
        hull() {
            linear_extrude(0.01)
                _shaft_profile(shaft_sq);
            translate([0, 0, collar_bevel])
                cylinder(d = collar_diameter, h = 0.01);
        }
        // Collar extends as a cylinder through flange and body to teeth base
        translate([0, 0, collar_bevel])
            cylinder(d = collar_diameter, h = ds_collar_h + flange_h + body_h - collar_bevel);
    }
}

// Flange — 2mm thick ring, 28.5mm OD / 21.5mm ID (mechanical stop, hollow centre)
module flange() {
    translate([0, 0, z_flange])
    difference() {
        cylinder(d = flange_d, h = flange_h);
        translate([0, 0, -0.1])
            cylinder(d = body_inner_d, h = flange_h + 0.2);
    }
}

// Body — 8mm hollow cylindrical section, 25.5mm OD, 2mm walls
module body() {
    translate([0, 0, z_body])
    difference() {
        cylinder(d = body_d, h = body_h);
        translate([0, 0, -0.1])
            cylinder(d = body_inner_d, h = body_h + 0.2);
    }
}

// Cylindrical boss inside body — provides solid material for square socket walls.
// collar() now extends through the flange zone, so no frustum bridge is needed.
module socket_boss() {
    translate([0, 0, z_body + socket_boss_gap])
        cylinder(d = socket_boss_d, h = body_h - socket_boss_gap + 0.1);
}

// Bevel gear teeth — conical transition from body_d to nose_d
// with 24 teeth. Tooth tips are flush with body and nose cylindrical
// edges; valleys are recessed inward by tooth_depth.
module bevel_teeth() {
    inner_bottom_r = body_d / 2 - tooth_depth;  // valley base (recessed from body OD)
    inner_top_r = nose_d / 2 - tooth_depth;     // valley top (recessed from nose OD)
    // tooth tips flush with body OD: body_d/2 = 12.75mm
    // tooth tips flush with nose OD: nose_d/2 = 8mm

    translate([0, 0, z_teeth]) {
        // Inner cone (dedendum surface — recessed from body/nose OD)
        cylinder(r1 = inner_bottom_r, r2 = inner_top_r, h = teeth_h);

        // Individual teeth protruding outward
        for (i = [0:num_bevel_teeth-1]) {
            angle = i * 360 / num_bevel_teeth;

            // Tooth width proportional to circumference at each level
            bottom_tooth_w = 3.14159 * inner_bottom_r * 2 / num_bevel_teeth * 0.45;
            top_tooth_w = 3.14159 * inner_top_r * 2 / num_bevel_teeth * 0.45;

            hull() {
                // Bottom face of tooth
                rotate([0, 0, angle])
                translate([inner_bottom_r, 0, 0])
                rotate([90, 0, 0])
                    linear_extrude(bottom_tooth_w, center = true)
                        square([tooth_depth, 0.01]);

                // Top face of tooth
                rotate([0, 0, angle])
                translate([inner_top_r, 0, teeth_h])
                rotate([90, 0, 0])
                    linear_extrude(top_tooth_w, center = true)
                        square([tooth_depth, 0.01]);
            }
        }
    }
}

// Nose — 8mm smooth cylinder, 16mm OD (13mm ID bore subtracted in assembly)
module nose() {
    translate([0, 0, z_nose])
        cylinder(d = nose_d, h = nose_h);
}

// Internal bore — 4mm diameter, extends from bottom face through shaft,
// collar, and bore_extra mm above the flange base within the flange.
// bore_d (4mm) < cyl_d (6mm), so 1mm of material remains around the bore
// in the bottom cylindrical piece. The collar cylinder provides solid material
// through the flange and body zones up to z=29.5.
module bore() {
    bore_h = cyl_h + ds_shaft_h + ds_collar_h + bore_extra;  // extends bore_extra mm above flange base
    translate([0, 0, -0.1])
        cylinder(d = bore_d, h = bore_h + 0.1);
}

// ---- Assembly ----
difference() {
    union() {
        ds_bottom_cylinder();
        ds_shaft();
        ds_collar();
        flange();
        body();           // hollow (2mm walls)
        socket_boss();    // inner column for socket walls
        bevel_teeth();
        nose();
    }

    // 4mm bore through bottom face, shaft, and collar to flange base
    bore();

    // 13mm circular bore through the nose
    translate([0, 0, z_nose - 0.1])
        cylinder(d = nose_inner_d, h = nose_h + 0.2);

    // Female square socket at top — opens at z=total_height,
    // extends 21mm downward to z=24.5 (inside body)
    translate([0, 0, total_height])
        mirror([0, 0, 1])
            square_socket();
}
