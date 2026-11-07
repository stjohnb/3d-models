// =====================================
// Hex Connector Library
// Single-piece connector — 7mm across-flats
// Female socket (10mm deep) at bottom, male protrusion (10mm) at top
// Total height: 30mm (20mm body + 10mm protrusion)
// =====================================

// === Parameters (mm) ===
hex_af       = 7.0;   // across-flats of socket and protrusion
wall         = 2;     // wall thickness around female socket
total_height = 20;    // outer body height
socket_depth = 10;    // female socket depth = male protrusion height
clearance    = 0.3;   // diametral fit clearance (0.15mm per side)
tip_bevel    = 0.8;   // taper height at male protrusion tip for insertion guide
bevel_radial = 0.8;   // circumradius reduction at protrusion tip

// Derived
outer_af = hex_af + 2 * wall;                        // 11.0mm
hex_r    = hex_af              / (2 * cos(30));      // circumradius for 7mm af
outer_r  = outer_af            / (2 * cos(30));      // circumradius for 11mm af
socket_r = (hex_af + clearance) / (2 * cos(30));     // socket circumradius with clearance
bevel_r  = hex_r - bevel_radial;                     // reduced circumradius at protrusion tip

// === Modules ===
module hex_prism(r, h) {
    rotate([0, 0, 30])
        cylinder(r = r, h = h, $fn = 6);
}

module hex_connector() {
    union() {
        difference() {
            hex_prism(outer_r, total_height);
            translate([0, 0, -0.01])
                hex_prism(socket_r, socket_depth + 0.01);
        }
        translate([0, 0, total_height]) {
            hex_prism(hex_r, socket_depth - tip_bevel);
            translate([0, 0, socket_depth - tip_bevel])
                hull() {
                    rotate([0, 0, 30]) cylinder(r = hex_r,   h = 0.01, $fn = 6);
                    translate([0, 0, tip_bevel])
                        rotate([0, 0, 30]) cylinder(r = bevel_r, h = 0.01, $fn = 6);
                }
        }
    }
}
