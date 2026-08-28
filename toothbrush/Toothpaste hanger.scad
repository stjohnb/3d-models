// =====================================
// Cap-Up Toothpaste Hanger Piece
// Backing block + dovetail channel + cap-neck fork; hooks onto the existing
// backplate's toothpaste rail in place of "Toothpaste clip.scad"
// Print with the dovetail channel face down on the bed — prongs point up
// =====================================

include <_toothbrush_holder.scad>

rotate([180, 0, 0])
translate([0, 0, -(grip_outer_x - plate_thickness)])
    paste_hanger_piece();
