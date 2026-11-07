// =====================================
// Ukulele Wall Hook
// Wall-mounted yoke that cradles a ukulele neck behind the headstock.
// Authored plate-upright (plate tall in +Z); no viewer rotation applied.
// Wall-facing surface is the Y=0 face; two screws pass through along +Y.
// =====================================

$fn = 64;

// ---- Parameters (mm) ----
plate_w      = 50;   // plate width (X)
plate_h      = 70;   // plate height (Z)
plate_t      = 8;    // plate thickness (Y)
corner_r     = 5;    // rounded plate-corner radius

screw_r      = 2.6;  // wall-screw shaft clearance (~#8 / 5mm screw)
screw_head_r = 5.5;  // counterbore radius (screw head clearance)
screw_cbore  = 3;    // counterbore depth from front face
screw_spacing = 45;  // vertical center-to-center of the two screw holes (Z)

prong_r      = 7;    // prong (capsule) radius
prong_len    = 55;   // prong projection from plate face (+Y)
prong_rise   = 22;   // prong tip rise above its root (+Z)
tip_up       = 18;   // upturned end segment height (+Z)
root_gap     = 30;   // center-to-center of prong roots (X)
// tip_gap sets the neck-cradle opening: clear width = tip_gap - 2*prong_r.
// Ukulele necks narrow to ~36mm at the nut (issue #293 review); keep this
// several mm above that so the neck drops in without binding.
tip_gap      = 56;   // center-to-center of prong tips (X)
prong_root_z = plate_h * 0.4;  // Z of prong roots on the plate

// Prong root flare — the arm/plate junction is the load-bearing section and
// the failure point (issue #390). root_r > prong_r widens that section and
// blends the sharp corner where the capsule met the flat plate face.
root_r       = 9.5;  // prong radius where it meets the plate
flare_len    = 20;   // distance along the prong axis over which root_r tapers to prong_r

// ---- Derived ----
screw_z_lo = plate_h/2 - screw_spacing/2;
screw_z_hi = plate_h/2 + screw_spacing/2;

// ---- Modules ----
module rounded_plate() {
    // Rounded rectangle in the X-Z face, thin in Y.
    hull() {
        for (x = [-plate_w/2 + corner_r, plate_w/2 - corner_r])
            for (z = [corner_r, plate_h - corner_r])
                translate([x, 0, z])
                    rotate([-90, 0, 0])
                        cylinder(r = corner_r, h = plate_t);
    }
}

module screw_hole(z) {
    // Through shaft hole + front-face counterbore, along +Y.
    translate([0, -0.1, z])
        rotate([-90, 0, 0])
            cylinder(r = screw_r, h = plate_t + 0.2);
    translate([0, plate_t - screw_cbore, z])
        rotate([-90, 0, 0])
            cylinder(r = screw_head_r, h = screw_cbore + 0.1);
}

module capsule(p0, p1, r0 = prong_r, r1 = prong_r) {
    hull() {
        translate(p0) sphere(r = r0);
        translate(p1) sphere(r = r1);
    }
}

// Root sphere center's Y offset: must be >= root_r so the root sphere's back
// pole never crosses Y=0 (the wall-facing mounting surface) — a smaller offset
// lets it punch a bump through the back face. Still overlaps rounded_plate
// (Y in [0, plate_t]) for a manifold union. Derived from root_r, not a literal,
// so a customizer -Droot_r=... override cannot break the back face.
prong_root_y = root_r + 0.5;

module prong(sx) {
    // sx = +1 or -1 (which side). Root embedded in plate for a manifold union.
    root  = [sx * root_gap/2, prong_root_y,       prong_root_z];
    elbow = [sx * tip_gap/2,  plate_t + prong_len, prong_root_z + prong_rise];
    tip   = [sx * tip_gap/2,  plate_t + prong_len, prong_root_z + prong_rise + tip_up];
    axis  = elbow - root;
    flare_end = root + axis / norm(axis) * flare_len;
    capsule(root, flare_end, root_r, prong_r);  // flared root — see issue #390
    capsule(flare_end, elbow);
    capsule(elbow, tip);
}

// ---- Assembly ----
// Screw holes are differenced from the WHOLE part, not just the plate: at
// customizer extremes (small plate_h with small screw_spacing, or a raised
// root_r) a flared root can reach the upper/lower counterbore, and cutting
// the plate first would let the prong union fill it back in.
difference() {
    union() {
        rounded_plate();
        prong(1);
        prong(-1);
    }
    screw_hole(screw_z_lo);
    screw_hole(screw_z_hi);
}
