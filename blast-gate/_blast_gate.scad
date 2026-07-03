// =====================================
// Blast Gate — Shared Library
// Inline sliding blast gate for 51mm OD PVC workshop vacuum lines.
// Sliding blade opens or closes airflow to dust-collection branches.
//
// Coordinate system:
//   Pipe axis: Z. Blade slides along X (handle exits at −X).
//   Slot lies in the X–Y plane, slot_h tall in Z.
//
// bore_d matches socket_id so the body bore is flush with the socket bore (no dust ledge).
//
// Print notes:
//   Body: print with pipe axis vertical (Z-up); slot is horizontal.
//   Supports may be needed to bridge the bore opening at the slot ceiling.
//   Blade: print flat on the build plate.
//
// Stop bump (prevents blade pulling fully out of slot) is omitted in v1.0.0.
// Add a bump on the blade leading edge if desired.
// =====================================

$fn = 64;

// === Parameters (mm) ===

// Pipe
pvc_od           = 51;     // PVC pipe outer diameter — widened 1 mm for slip fit on 50 mm nominal pipe
socket_clearance = 0.4;    // diametral slip-fit clearance on socket bore
socket_id        = pvc_od + socket_clearance;  // 51.4
socket_wall      = 2.5;
socket_od        = socket_id + 2*socket_wall;  // 56.4
socket_length    = 25;     // pipe insertion depth per side

// Internal flow bore: matches socket_id so no ledge forms at the socket/body junction
bore_d           = socket_id;

// Body block (square cross-section, slot through the middle)
frame            = 8;                    // material thickness around bore
body_w           = bore_d + 2*frame;    // Y extent (perpendicular to blade slide)
body_d           = bore_d + 2*frame;    // X extent (along blade slide direction)
plate_t          = 4;                   // plate thickness above/below the slot
end_wall         = 4;                   // closed-end wall at +X joining top/bottom plates; slot open at −X for blade entry
slot_h           = 3.4;                 // gate_thickness + 0.4mm total clearance
body_h           = 2*plate_t + slot_h;  // 11.4 — Z extent between socket bases

// Blade
gate_thickness   = 3;
y_rail           = 2;                  // Y-wall reserve per side; printed wall = y_rail − 0.2 after slot clearance
blade_w          = body_w - 2*y_rail; // narrower than body so Y walls remain intact
blade_travel     = bore_d + 6;         // travel so solid blade fully covers bore
blade_l          = body_d - end_wall;  // spans exactly the slot length in X
handle_w         = blade_w;
handle_t         = 8;                  // handle depth in X
handle_l         = 25;                 // handle height in Z (perpendicular to blade plane)

// Mounting plate (opposite blade-exit side, at +X end of body block)
mount_plate_t      = 4;                           // plate thickness in X
mount_plate_margin = 10;                          // extends this far beyond body_block on Y and Z per side
mount_plate_w      = body_w + 2*mount_plate_margin;
mount_plate_h      = body_h + 2*mount_plate_margin;
mount_hole_d       = 4;                           // M4 / #8 screw clearance
mount_hole_inset   = 5;                           // hole-centre distance from plate edge

// Catch notches (blade-closed retention)
catch_notch_depth = 0.8;  // depth into Y-wall (mm); keeps ≥1 mm of wall remaining
catch_notch_width = 3.0;  // notch extent along X (blade travel direction)
catch_bump_h      = catch_notch_depth - 0.1;  // bump protrusion from blade edge; 0.1 mm clearance at notch far wall

// === Modules ===

// One pipe socket. z_base: Z coordinate of the socket base face.
module socket_stub(z_base) {
    translate([0, 0, z_base])
        difference() {
            cylinder(d=socket_od, h=socket_length);
            translate([0, 0, -0.1])
                cylinder(d=socket_id, h=socket_length + 0.2);
        }
}

// Central body block: plate material above and below the blade slot.
module body_block() {
    difference() {
        cube([body_d, body_w, body_h], center=true);
        // Bore cylinder along pipe axis (Z)
        cylinder(d=bore_d, h=body_h + 1, center=true);
        // Blade slot: open at -X (blade entry), closed at +X by end_wall; Y side walls remain
        translate([-body_d/2 - 1, -(blade_w + 0.4)/2, -slot_h/2])
            cube([body_d + 1 - end_wall, blade_w + 0.4, slot_h]);
        // Catch notches: small recesses in Y-walls at the fully-closed blade position.
        // When the blade is pushed in, its edges snap into these wider pockets and
        // resist sliding back open under vibration.
        for (y_sign = [-1, 1]) {
            translate([body_d/2 - end_wall - catch_notch_width,
                       y_sign > 0 ? (blade_w + 0.4)/2 : -(blade_w + 0.4)/2 - catch_notch_depth,
                       -gate_thickness/2])
                cube([catch_notch_width, catch_notch_depth, gate_thickness]);
        }
    }
}

// Full gate body: central block plus top and bottom pipe sockets.
module gate_body() {
    union() {
        body_block();
        socket_stub(body_h/2);                  // top socket
        socket_stub(-body_h/2 - socket_length); // bottom socket
        mount_plate();
    }
}

// Mounting plate on the +X (closed-end) face, opposite the blade-exit opening.
// Screw holes pass through the plate along X (perpendicular to the mounting surface).
module mount_plate() {
    translate([body_d/2, 0, 0])
    difference() {
        translate([0, -mount_plate_w/2, -mount_plate_h/2])
            cube([mount_plate_t, mount_plate_w, mount_plate_h]);
        for (y_sign = [-1, 1]) {
            for (z_sign = [-1, 1]) {
                translate([-0.1,
                           y_sign * (mount_plate_w/2 - mount_hole_inset),
                           z_sign * (mount_plate_h/2 - mount_hole_inset)])
                    rotate([0, 90, 0])
                        cylinder(d=mount_hole_d, h=mount_plate_t + 0.2);
            }
        }
    }
}

// Sliding blade. Origin at trailing edge (handle side); leading edge at X = blade_l.
// Push blade IN (+X) to close (solid plate covers bore). Pull OUT (−X) by blade_travel
// to open (leading edge clears the bore). No through-hole needed.
module gate_blade() {
    // Blade plate: trailing edge at X=0, leading edge at X=blade_l, centered in Y and Z
    translate([0, -blade_w/2, -gate_thickness/2])
        cube([blade_l, blade_w, gate_thickness]);

    // Handle: perpendicular tab at trailing edge, centered on blade face in Z
    translate([-handle_t, -handle_w/2, -handle_l/2])
        cube([handle_t, handle_w, handle_l]);

    // Catch bumps: protrude in Y at the leading edge, snapping into body catch notches at closed position
    for (y_sign = [-1, 1])
        translate([blade_l - catch_notch_width,
                   y_sign > 0 ? blade_w/2 : -blade_w/2 - catch_bump_h,
                   -gate_thickness/2])
            cube([catch_notch_width, catch_bump_h, gate_thickness]);
}
