// =====================================
// ESP32-2432S028R display case ("Cheap Yellow Display" / CYD)
// Two-part snap-fit enclosure for the 2.8" 240x320 resistive-touch TFT board,
// with an integrated snap-in holder for the bundled touchscreen stylus.
// =====================================
// Parts:
//   case_back  -> case_back.stl   (rear shell + two stylus saddle clips)
//   case_front -> case_front.stl  (front bezel with display window + snap skirt)
//
// Orientation: both parts are modeled upright in print orientation (Z-up),
// origin-centred on X/Y with their base at z=0. No viewer rotation is applied
// (analogous to sink-tray / hex-connector).
//
// Board dimensions are published CYD community specs, NOT calipered — they are
// flagged "VERIFY w/ calipers" below and exposed as customizer parameters, so a
// test print should confirm board fit before a final print. The stylus numbers
// (pen_*) ARE measured from the caliper photos in issue #268.

$fn = 64;

// === Parameters (mm) ===

// --- Board (VERIFY w/ calipers; published ESP32-2432S028R specs) ---
board_w         = 50.5;  // PCB short-edge width (spec ~50.3)
board_l         = 86.5;  // PCB long-edge length (spec ~86.4)
pcb_thickness   = 1.7;
component_depth = 13;    // cavity depth below PCB back for ESP32/USB/JST

// --- Fit / walls ---
fit_clearance   = 0.4;   // total slack board-edge to wall (0.2/side)
wall            = 2.4;
corner_r        = 3;
post_size       = 5;     // corner support-post footprint (square)

// --- Front bezel ---
bezel_thickness = 2.4;
skirt_depth     = 6;
skirt_wall      = 2.0;
skirt_clearance = 0.3;

// --- Display window (2.8" active ~43.2 x 57.6; VERIFY) ---
window_w        = 44;
window_l        = 58;
window_off_w    = 0;
window_off_l    = 0;

// --- Wall port cutouts (generous; connector positions unknown) ---
corner_margin   = 8;     // solid material at each wall end
floor_rail      = 1.2;   // thin rail at bottom of each side cutout

// --- Touchscreen stylus holder (measured w/ calipers) ---
pen_holder      = true;  // toggle the stylus clips
pen_dia         = 4.1;   // stylus shaft diameter (measured 4.07)
pen_clip_clear  = 0.3;   // radial slack, clip bore vs shaft
pen_clip_grip   = 220;   // clip arc sweep, degrees (>180 retains the pen)
pen_clip_wall   = 1.6;   // clip wall thickness
pen_clip_len    = 9;     // length of each clip along the pen axis
pen_clip_span   = 55;    // center-to-center distance between the two clips
pen_clip_z      = 5;     // clip center height above shell floor

// === Derived ===
inner_w  = board_w + fit_clearance;
inner_l  = board_l + fit_clearance;
outer_w  = inner_w + 2 * wall;
outer_l  = inner_l + 2 * wall;
cavity_h = component_depth + pcb_thickness;
shell_h  = wall + cavity_h;

pen_ri = pen_dia / 2 + pen_clip_clear;   // clip bore radius
pen_ro = pen_ri + pen_clip_wall;         // clip outer radius

// Side-wall vent slot: from just above the floor rail up to the top rim.
vent_z0 = wall + floor_rail;
vent_h  = shell_h - vent_z0 + 0.1;
// The long (X) walls carry the stylus clips, so their vent is kept short enough
// to sit between the two clip footprints; the short (Y) walls vent the full
// span less the corner margins.
xvent_l = pen_holder ? max(0, pen_clip_span - pen_clip_len - 2)
                     : outer_l - 2 * corner_margin;
yvent_l = outer_w - 2 * corner_margin;

// === Modules ===

// Rounded-rect vertical prism: hull of four corner cylinders.
// Centred on X/Y, base at z=0.
module rbox(w, l, h, r) {
    hull()
        for (sx = [-1, 1], sy = [-1, 1])
            translate([sx * (w/2 - r), sy * (l/2 - r), 0])
                cylinder(r = r, h = h);
}

// One stylus saddle clip. Axis along Y, centred at origin, mouth opening
// facing +Z so the pen drops in from above (support-free print).
// The C wraps pen_clip_grip degrees; the top opening is 360 - pen_clip_grip.
module pen_clip(len) {
    // Mouth half-width, measured at the pen surface so the opening is narrower
    // than the pen (and therefore retains it) exactly when pen_clip_grip > 180.
    hw = (pen_dia / 2) * sin((360 - pen_clip_grip) / 2);
    difference() {
        rotate([90, 0, 0]) cylinder(r = pen_ro, h = len, center = true);
        // Bore (overshoot both ends in Y)
        rotate([90, 0, 0]) cylinder(r = pen_ri, h = len + 0.2, center = true);
        // Cut the top opening: remove the top region within the mouth width.
        translate([0, 0, (pen_ro + 1) / 2])
            cube([2 * hw, len + 0.2, pen_ro + 1], center = true);
    }
}

// Rear shell: origin-centred, base at z=0, opening toward +Z. Holds the board
// components and carries the two stylus clips on the +X long wall.
module case_back() {
    union() {
        difference() {
            // Outer solid
            rbox(outer_w, outer_l, shell_h, corner_r);

            // Interior cavity (from top of the floor up)
            translate([0, 0, wall])
                rbox(inner_w, inner_l, cavity_h + 0.1, max(0.5, corner_r - wall));

            // Side-wall port/vent cutouts — one centred per wall, cut fully
            // through the wall, floor_rail retained at the bottom.
            // +/-X long walls (span along Y); kept clear of the stylus clips.
            for (sx = [-1, 1])
                translate([sx * (inner_w/2 + wall/2), 0, vent_z0 + vent_h/2])
                    cube([wall + 0.2, xvent_l, vent_h], center = true);
            // +/-Y short walls (span along X)
            for (sy = [-1, 1])
                translate([0, sy * (inner_l/2 + wall/2), vent_z0 + vent_h/2])
                    cube([yvent_l, wall + 0.2, vent_h], center = true);
        }

        // Corner support posts (added after the cavity cut so they stand
        // inside it). Outer faces sit flush with the cavity walls and fuse.
        for (sx = [-1, 1], sy = [-1, 1])
            translate([sx * (inner_w/2 - post_size/2),
                       sy * (inner_l/2 - post_size/2),
                       wall + component_depth/2])
                cube([post_size, post_size, component_depth], center = true);

        // Stylus clips on the +X exterior long wall. The -0.8 overlap sinks the
        // clip's outer arc into the wall so it fuses.
        if (pen_holder)
            for (sy = [-1, 1])
                translate([outer_w/2 + pen_ro - 0.8, sy * pen_clip_span/2, pen_clip_z])
                    pen_clip(pen_clip_len);
    }
}

// Front bezel: origin-centred, skirt bottom at z=0. A faceplate with a display
// window and a downward skirt that snaps over the rear shell exterior.
module case_front() {
    difference() {
        union() {
            // Faceplate cap
            translate([0, 0, skirt_depth])
                rbox(outer_w, outer_l, bezel_thickness, corner_r);

            // Skirt: outer wall minus the shell-shaped cavity it slides over
            difference() {
                rbox(outer_w + 2 * skirt_wall, outer_l + 2 * skirt_wall,
                     skirt_depth + bezel_thickness, corner_r + skirt_wall);
                translate([0, 0, -0.05])
                    rbox(outer_w + skirt_clearance, outer_l + skirt_clearance,
                         skirt_depth + 0.1, corner_r);
            }
        }

        // Display window through the faceplate
        translate([window_off_w, window_off_l, skirt_depth + bezel_thickness/2])
            cube([window_w, window_l, bezel_thickness + 1], center = true);
    }
}

// Rendered individually:
//   case_back.scad  -> case_back.stl
//   case_front.scad -> case_front.stl
