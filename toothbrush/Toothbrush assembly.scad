// =====================================
// Toothbrush Assembly Preview
// Shows holder and drip tray fitted together
// =====================================

include <_toothbrush_holder.scad>
use <Toothbrush tray.scad>

// Peg center X positions on the base
peg_x1 = base_length/2 - plate_center_x - grip_spacing/2;
peg_x2 = base_length/2 - plate_center_x + grip_spacing/2;
tray_center_x = (peg_x1 + peg_x2) / 2;

// ---- Assembly ----
// Rotate to Y-up for Three.js viewer
rotate([-90, 0, 0])
union() {
    toothbrush_holder();

    // Tray sits on the base pegs, centered over them
    translate([tray_center_x, peg_y, base_height + outer_bottom_radius])
        drip_tray();
}
