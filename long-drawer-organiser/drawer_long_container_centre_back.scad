// Long Drawer Organiser — back five cells of the unflared diagonal container
// Render this file to generate drawer_long_container_centre_back.stl
// 167.25 x 209.75mm. Print ONE; glue to _centre_front.
// No rotate(): sources stay OpenSCAD Z-up; the viewer applies the Z-up -> Y-up conversion itself.

include <_drawer_long.scad>

height  = 69;         // overall height above the drawer floor (mm); the drawer is 69mm tall
wall_t  = 1.6;        // wall thickness (mm)
floor_t = 1.6;        // floor thickness above the base pads (mm)

long_diag_container_slice(4, 10, height, wall_t, floor_t, side = 1, cx = long_span_x(long_centre_cols), c0 = 5, c1 = 10);
