// =====================================
// Fisher-Price Power Workshop - Shared Connection
// Common square-peg connection shared by all attachments
// See CONNECTION_SPEC.md for measurement details
// =====================================

// ---- Connection Parameters (mm) ----

// Square shaft (male end - plugs into handle)
// Measured from calipers on existing attachment
shaft_sq = 8.2;          // side length
shaft_sq_length = 12.4;  // total length of square shaft (3.5 + 3.1 + 5.8)

// Snap groove in the square shaft
groove_pos = 3.5 + 3.1/2;   // from tip (z=0) to groove center
groove_width = 3.1;      // width of the groove
groove_depth = 0.95;     // per side: (8.2 - 6.3) / 2
groove_bevel = 0.8;      // taper height at each end of groove
tip_bevel = 0.8;         // taper height at tip for insertion guide
corner_r = 1.0;          // corner rounding radius on male shaft (mimics injection-molded originals)

// Transition collar
collar_diameter = 12.5;  // measured
collar_length = 8.3;     // measured
collar_bevel = 2.0;      // taper from square shaft to round collar

// Square socket (female end - accepts male shaft)
// Sized to accept shaft with clearance
socket_size = 8.6;      // side length (+0.4mm clearance over 8.2mm shaft)
socket_depth = 13;      // depth of square socket (accepts 12.4mm shaft)
socket_lead_in = 1.2;   // chamfer depth at the opening to reduce catching

// Snap ridge inside socket (mates with groove on attachments)
ridge_pos = 7.35;       // from opening; aligns with groove when shaft inserted
ridge_width = 3.1;      // matches groove width
ridge_depth = 0.95;     // matches groove depth
ridge_bevel = 0.8;      // taper height at each end of ridge (matches groove_bevel)

// ---- Connection Modules ----

// 2D profile for corner-only snap ridge.
// Intersecting the socket square with a 45-degree-rotated square creates an
// octagon — material protrudes only at the four corners, allowing the shaft
// to push past with moderate force while still snapping into the groove for
// retention.
module _ridge_profile() {
    intersection() {
        square(socket_size, center=true);
        rotate([0, 0, 45])
            square(socket_size * sqrt(2) - ridge_depth * 2, center=true);
    }
}

// 2D rounded-square profile for male shaft cross-sections.
// Shrinks inward then rounds back outward so the result is the same side
// length with corners rounded at corner_r radius.
module _shaft_profile(size) {
    offset(r = corner_r) offset(delta = -corner_r)
        square(size, center = true);
}

// Square plug shaft with snap groove and beveled transitions
module sq_shaft() {
    groove_start = groove_pos - groove_width/2;
    groove_end = groove_pos + groove_width/2;
    groove_sq = shaft_sq - groove_depth * 2;

    // Tip bevel (matches groove transition style)
    hull() {
        linear_extrude(0.01)
            _shaft_profile(groove_sq);
        translate([0, 0, tip_bevel])
            linear_extrude(0.01)
                _shaft_profile(shaft_sq);
    }

    // Remaining tip section
    translate([0, 0, tip_bevel])
        linear_extrude(groove_start - groove_bevel - tip_bevel)
            _shaft_profile(shaft_sq);

    // Bevel into groove
    hull() {
        translate([0, 0, groove_start - groove_bevel])
            linear_extrude(0.01)
                _shaft_profile(shaft_sq);
        translate([0, 0, groove_start])
            linear_extrude(0.01)
                _shaft_profile(groove_sq);
    }

    // Groove
    translate([0, 0, groove_start])
        linear_extrude(groove_width)
            _shaft_profile(groove_sq);

    // Bevel out of groove
    hull() {
        translate([0, 0, groove_end])
            linear_extrude(0.01)
                _shaft_profile(groove_sq);
        translate([0, 0, groove_end + groove_bevel])
            linear_extrude(0.01)
                _shaft_profile(shaft_sq);
    }

    // Main shaft
    translate([0, 0, groove_end + groove_bevel])
        linear_extrude(shaft_sq_length - groove_end - groove_bevel)
            _shaft_profile(shaft_sq);
}

// Square socket with snap ridge and beveled transitions
// Includes a chamfered lead-in at the opening to reduce insertion catching
module square_socket() {
    ridge_start = ridge_pos - ridge_width/2;
    ridge_end = ridge_pos + ridge_width/2;

    // Lead-in chamfer at opening — wider at the entrance, tapers to socket_size at depth
    translate([0, 0, -0.1])
        linear_extrude(socket_lead_in + 0.1, scale = socket_size / (socket_size + 0.8))
            square(socket_size + 0.8, center = true);

    // Below ridge (full-size socket)
    translate([0, 0, socket_lead_in])
        linear_extrude(ridge_start - ridge_bevel - socket_lead_in)
            square(socket_size, center = true);

    // Bevel into ridge
    hull() {
        translate([0, 0, ridge_start - ridge_bevel])
            linear_extrude(0.01)
                square(socket_size, center = true);
        translate([0, 0, ridge_start])
            linear_extrude(0.01)
                _ridge_profile();
    }

    // Ridge section (corner-only octagonal profile)
    translate([0, 0, ridge_start])
        linear_extrude(ridge_width)
            _ridge_profile();

    // Bevel out of ridge
    hull() {
        translate([0, 0, ridge_end])
            linear_extrude(0.01)
                _ridge_profile();
        translate([0, 0, ridge_end + ridge_bevel])
            linear_extrude(0.01)
                square(socket_size, center = true);
    }

    // Above ridge to full depth
    translate([0, 0, ridge_end + ridge_bevel])
        linear_extrude(socket_depth - ridge_end - ridge_bevel + 0.1)
            square(socket_size, center = true);
}

// Transition collar with beveled square-to-round base
module collar() {
    translate([0, 0, shaft_sq_length - 0.01]) {  // -0.01mm overlap with shaft top prevents coplanar faces
        // Taper from square shaft to round collar
        hull() {
            linear_extrude(0.01)
                _shaft_profile(shaft_sq);
            translate([0, 0, collar_bevel])
                cylinder(d = collar_diameter, h = 0.01);
        }
        // Remaining collar
        translate([0, 0, collar_bevel])
            cylinder(d = collar_diameter, h = collar_length - collar_bevel);
    }
}
