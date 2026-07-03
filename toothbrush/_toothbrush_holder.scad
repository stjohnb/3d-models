// =====================================
// Toothbrush Holder Library
// Shared parameters and modules for the toothbrush/toothpaste holder system
// Two toothbrush clips + one toothpaste clip on a vertical backplate
// Solid base with alignment pegs for drip tray
// Toothbrush cross-section: 29mm (front-to-back) x 28mm (side-to-side)
// Toothpaste clip: 50x15mm rounded rectangle, 40mm front gap, 5mm band height
// =====================================

// ---- Clip Parameters (mm) ----
width           = 30;

grip_inner_x    = 29;       // toothbrush front-to-back diameter
grip_inner_y    = 28;       // toothbrush side-to-side diameter
grip_wall       = 2;
grip_outer_x    = grip_inner_x + 2 * grip_wall;  // 33
grip_outer_y    = grip_inner_y + 2 * grip_wall;  // 32
grip_outer_rx   = grip_outer_x / 2;               // 16.5
grip_outer_ry   = grip_outer_y / 2;               // 16
grip_inner_rx   = grip_inner_x / 2;               // 14.5
grip_inner_ry   = grip_inner_y / 2;               // 14

// Toothpaste clip parameters (rounded rectangle, tapered)
paste_inner_w_top = 50;        // inner width at top (side-to-side)
paste_inner_w_bot = 45;        // inner width at bottom
paste_inner_d   = 15;          // inner depth (front-to-back)
paste_corner_r  = 3;           // corner radius for rounded rectangle
paste_outer_w_top = paste_inner_w_top + 2 * grip_wall;  // 54
paste_outer_w_bot = paste_inner_w_bot + 2 * grip_wall;  // 49
paste_outer_w   = paste_outer_w_top;  // for plate sizing (widest)
paste_outer_d   = paste_inner_d + 2 * grip_wall;  // 19
paste_gap_top   = 40;          // front gap width at top
paste_gap_bot   = 35;          // front gap width at bottom

plate_thickness = 3;
plate_corner_r  = width / 2;   // fully rounded ends (stadium shape)

opening_angle   = 100;         // bottom opening of each clip (degrees)
grip_spacing    = 40;          // center-to-center distance between toothbrush grips
paste_offset    = -70;         // toothpaste clip center X position (left of toothbrush clips)

// ---- Base Parameters ----
base_length     = 168;
base_depth      = 55;
base_height     = 5;
base_corner_r   = 3;

// ---- Alignment Peg Parameters ----
peg_length      = 20;          // X dimension
peg_width       = 4;           // Y dimension
peg_height      = 2;           // Z dimension
peg_chamfer     = 0.5;         // top edge chamfer
peg_y           = 30;          // Y position (forward of stand to clear tray)

// ---- Tray Parameters ----
outer_bottom_radius = 1.5;     // tray outer bottom fillet radius

// ---- Stand & Derived Parameters ----
stand_width     = 40;
brush_top_z     = 130;         // toothbrush clips: 100-130mm
paste_top_z     = 190;         // toothpaste clip: 160-190mm
clip_forward    = 10;          // how far clips are moved forward from backplate
arm_width       = 8;           // X dimension of connecting arms
arm_height      = 8;           // Y dimension of connecting arms (becomes Z in assembly)

// ---- Dovetail Joint Parameters (mm) ----
dt_width_base   = 10;          // wide end (at front, away from plate — locks clip on)
dt_width_tip    = 7;           // narrow end (at plate face)
dt_depth        = 5;           // how far rail protrudes from plate
dt_clearance    = 0.15;        // clearance per side for fit
dt_stop         = 3;           // stopper thickness at top of rail

// Derived positions
stand_height    = paste_top_z - base_height;           // stand reaches highest clip

$fn = 64;

// ---- Ellipse module ----
module ellipse(rx, ry) {
    scale([rx, ry])
        circle(r = 1);
}

// ---- C-shaped clip ----
// Centered at origin, axis along Y, bottom of outer ellipse at z=0
module c_clip() {
    translate([0, 0, grip_outer_rx])
    rotate([90, 0, 0])
    translate([0, 0, -width / 2])
    difference() {
        // Ring
        linear_extrude(width)
            difference() {
                ellipse(grip_outer_rx, grip_outer_ry);
                ellipse(grip_inner_rx, grip_inner_ry);
            }

        // Bottom wedge cutout
        R = grip_outer_rx + 1;
        translate([0, 0, -0.5])
        linear_extrude(width + 1)
            polygon([
                [0, 0],
                [-R * sin(opening_angle / 2), -R * cos(opening_angle / 2)],
                [-R, -R],
                [ R, -R],
                [ R * sin(opening_angle / 2), -R * cos(opening_angle / 2)]
            ]);
    }
}

// ---- Toothpaste clip (rounded rectangle, tapered) ----
// Full height of top plate, tapering from 50mm wide at top to 45mm at bottom
// Profile XY: X = width (side-to-side), +Y = top (plate), -Y = bottom (gap)
// Taper is in the 2D profile, extruded uniformly along Z (both sides identical)
module paste_clip() {
    translate([0, 0, grip_outer_x - paste_outer_d / 2])
    rotate([90, 0, 0])
    translate([0, 0, -width / 2])
    difference() {
        // Tapered outer shell: wider at +Y (top), narrower at -Y (bottom)
        linear_extrude(width)
        hull() {
            // Top corners (wide)
            for (x = [-(paste_outer_w_top/2 - paste_corner_r),
                       (paste_outer_w_top/2 - paste_corner_r)])
                translate([x, paste_outer_d/2 - paste_corner_r])
                    circle(r = paste_corner_r);
            // Bottom corners (narrow)
            for (x = [-(paste_outer_w_bot/2 - paste_corner_r),
                       (paste_outer_w_bot/2 - paste_corner_r)])
                translate([x, -(paste_outer_d/2 - paste_corner_r)])
                    circle(r = paste_corner_r);
        }

        // Tapered inner cavity
        linear_extrude(width)
        hull() {
            for (x = [-(paste_inner_w_top/2 - paste_corner_r),
                       (paste_inner_w_top/2 - paste_corner_r)])
                translate([x, paste_inner_d/2 - paste_corner_r])
                    circle(r = paste_corner_r);
            for (x = [-(paste_inner_w_bot/2 - paste_corner_r),
                       (paste_inner_w_bot/2 - paste_corner_r)])
                translate([x, -(paste_inner_d/2 - paste_corner_r)])
                    circle(r = paste_corner_r);
        }

        // Tapered front gap cutout (wider at top, narrower at bottom)
        translate([0, 0, -0.5])
        linear_extrude(width + 1)
        hull() {
            // Top edge of gap (at Y=0, toward clip body): wider
            translate([0, 0])
                square([paste_gap_top, 0.01], center = true);
            // Bottom edge of gap (at Y=-paste_outer_d, opening): narrower
            translate([0, -paste_outer_d])
                square([paste_gap_bot, 0.01], center = true);
        }
    }
}

// ---- Plate geometry ----
// plate_center_x used for overall X positioning (centered between all clips)
plate_left  = paste_offset - paste_outer_w / 2 - plate_corner_r;
plate_right = grip_spacing / 2 + grip_outer_rx + plate_corner_r;
plate_center_x = (plate_left + plate_right) / 2;

// Brush plate spans the two toothbrush clips
brush_plate_left  = -grip_spacing / 2 - grip_outer_rx - plate_corner_r + 5;
brush_plate_right = grip_spacing / 2 + grip_outer_rx + plate_corner_r;
brush_plate_cx    = (brush_plate_left + brush_plate_right) / 2;  // 0 (symmetric)
brush_plate_len   = brush_plate_right - brush_plate_left;

// Paste plate spans from paste clip to stand (stand right in clip-local X)
stand_local_right = plate_center_x + stand_width / 2;
paste_plate_left  = paste_offset - paste_outer_w / 2 - plate_corner_r;
paste_plate_right = stand_local_right + plate_corner_r;
paste_plate_cx    = (paste_plate_left + paste_plate_right) / 2;
paste_plate_len   = paste_plate_right - paste_plate_left;

module brush_plate() {
    translate([brush_plate_cx, 0, grip_outer_x - plate_thickness])
    hull() {
        for (x = [-(brush_plate_len / 2 - plate_corner_r),
                    (brush_plate_len / 2 - plate_corner_r)])
            translate([x, 0, 0])
                cylinder(r = plate_corner_r, h = plate_thickness);
    }
}

module paste_plate() {
    translate([paste_plate_cx, 0, grip_outer_x - plate_thickness])
    hull() {
        for (x = [-(paste_plate_len / 2 - plate_corner_r),
                    (paste_plate_len / 2 - plate_corner_r)])
            translate([x, 0, 0])
                cylinder(r = plate_corner_r, h = plate_thickness);
    }
}

// ---- Solid base with rounded corners ----
module solid_base() {
    linear_extrude(base_height)
        offset(r = base_corner_r)
            square([base_length - 2 * base_corner_r,
                    base_depth - 2 * base_corner_r], center = true);
}

// ---- Alignment peg with chamfered top (origin at bottom, protrudes upward) ----
module alignment_peg() {
    hull() {
        // Full-size base (from Z=0 to Z=peg_height - peg_chamfer)
        translate([0, 0, (peg_height - peg_chamfer) / 2])
            cube([peg_length, peg_width, peg_height - peg_chamfer], center = true);
        // Chamfered top
        translate([0, 0, peg_height - peg_chamfer / 2])
            cube([peg_length - 2 * peg_chamfer,
                  peg_width - 2 * peg_chamfer,
                  peg_chamfer], center = true);
    }
}

// ---- Dovetail rail (male, on backplate) ----
// Centered in X, extends Y ±length/2
// Narrow (dt_width_tip) at Z=0 (plate face), wide (dt_width_base) at Z=-dt_depth (front)
// Wide front end locks clip onto plate — clip can only slide off along Y
module dovetail_rail(length) {
    translate([0, -length/2, 0])
    rotate([-90, 0, 0])
    linear_extrude(length)
        polygon([
            [-dt_width_tip/2, 0],
            [ dt_width_tip/2, 0],
            [ dt_width_base/2, dt_depth],
            [-dt_width_base/2, dt_depth]
        ]);
}

// ---- Dovetail channel (female, on clip piece) ----
// Same orientation as rail but enlarged by dt_clearance on all sides
module dovetail_channel(length) {
    cl = dt_clearance;
    translate([0, -length/2, 0])
    rotate([-90, 0, 0])
    linear_extrude(length)
        polygon([
            [-(dt_width_tip/2 + cl), -cl],
            [ (dt_width_tip/2 + cl), -cl],
            [ (dt_width_base/2 + cl), dt_depth + cl],
            [-(dt_width_base/2 + cl), dt_depth + cl]
        ]);
}

// ---- Brush clip piece (detachable: clip + arm + dovetail channel) ----
module brush_clip_piece() {
    dt_block_w = dt_width_base + 2 * grip_wall;
    z_plate_face = grip_outer_x - plate_thickness;
    z_arm_start = grip_outer_x - clip_forward - grip_wall;

    difference() {
        union() {
            translate([0, 0, -clip_forward]) c_clip();

            // Arm from clip back to dovetail block (full block width and height)
            translate([-dt_block_w/2, -width/2, z_arm_start])
                cube([dt_block_w, width, z_plate_face - z_arm_start]);
        }

        // Cut dovetail channel from back face
        translate([0, 0, z_plate_face])
            dovetail_channel(width + 1);
    }
}

// ---- Paste clip piece (detachable: clip + arm + dovetail channel) ----
module paste_clip_piece() {
    dt_block_w = dt_width_base + 2 * grip_wall;
    z_plate_face = grip_outer_x - plate_thickness;
    z_arm_start = grip_outer_x - clip_forward - grip_wall;

    difference() {
        union() {
            translate([0, 0, -clip_forward]) paste_clip();

            // Arm from clip back to dovetail block (full block width and height)
            translate([-dt_block_w/2, -width/2, z_arm_start])
                cube([dt_block_w, width, z_plate_face - z_arm_start]);
        }

        // Cut dovetail channel from back face
        translate([0, 0, z_plate_face])
            dovetail_channel(width + 1);
    }
}

// ---- Backplate with dovetail rails (for separate printing) ----
module toothbrush_backplate() {
    // Solid base
    translate([base_length / 2, base_depth / 2, 0])
        solid_base();

    // Alignment pegs
    for (brush_dx = [-grip_spacing/2, grip_spacing/2])
        translate([base_length/2 - plate_center_x + brush_dx,
                   peg_y,
                   base_height])
            alignment_peg();

    // Vertical stand
    translate([base_length/2 - stand_width/2, 0, base_height])
        cube([stand_width, plate_thickness, stand_height]);

    // Brush plates + dovetail rails + stops
    translate([base_length/2 - plate_center_x, grip_outer_x, brush_top_z - width/2])
    rotate([90, 0, 0])
    {
        brush_plate();
        dt_block_w = dt_width_base + 2 * grip_wall;
        for (dx = [-grip_spacing/2, grip_spacing/2]) {
            // Rail: shifted up by dt_stop/2 so bottom end leaves room for stop
            translate([dx, dt_stop/2, grip_outer_x - plate_thickness])
                dovetail_rail(width - dt_stop);
            // Stop block at bottom of rail (wider than channel, clip slides down from top)
            translate([dx - dt_block_w/2, -width/2,
                       grip_outer_x - plate_thickness - dt_depth])
                cube([dt_block_w, dt_stop, dt_depth]);
        }
    }

    // Paste plate + dovetail rail + stop
    translate([base_length/2 - plate_center_x, grip_outer_x, paste_top_z - width/2])
    rotate([90, 0, 0])
    {
        paste_plate();
        dt_block_w = dt_width_base + 2 * grip_wall;
        // Rail
        translate([paste_offset, dt_stop/2, grip_outer_x - plate_thickness])
            dovetail_rail(width - dt_stop);
        // Stop block at bottom
        translate([paste_offset - dt_block_w/2, -width/2,
                   grip_outer_x - plate_thickness - dt_depth])
            cube([dt_block_w, dt_stop, dt_depth]);
    }
}

// ---- Holder Assembly (Z-up, no viewer rotation) ----
module toothbrush_holder() {
    // Backplate with dovetail rails
    toothbrush_backplate();

    // Brush clip pieces in position
    translate([base_length/2 - plate_center_x, grip_outer_x, brush_top_z - width/2])
    rotate([90, 0, 0])
    {
        translate([-grip_spacing / 2, 0, 0]) brush_clip_piece();
        translate([ grip_spacing / 2, 0, 0]) brush_clip_piece();
    }

    // Paste clip piece in position
    translate([base_length/2 - plate_center_x, grip_outer_x, paste_top_z - width/2])
    rotate([90, 0, 0])
    {
        translate([paste_offset, 0, 0]) paste_clip_piece();
    }
}
