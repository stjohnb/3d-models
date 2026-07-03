// =====================================
// Toothpaste Clip Piece - Test Print
// Clip + arm + dovetail channel
// Print with dovetail channel face down on bed
// =====================================

include <_toothbrush_holder.scad>

// Dovetail back face at Z = grip_outer_x - plate_thickness = 30
// Rotate so back face is down, then shift to bed
rotate([180, 0, 0])
translate([0, 0, -(grip_outer_x - plate_thickness)])
    paste_clip_piece();
