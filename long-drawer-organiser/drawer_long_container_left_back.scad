// Long Drawer Organiser — back five cells of the flared diagonal container
// Render this file to generate drawer_long_container_left_back.stl
// 123.25 x 209.75mm. Print ONE; glue to _left_front.
// No rotate(): sources stay OpenSCAD Z-up; the viewer applies the Z-up -> Y-up conversion itself.

include <_drawer_long.scad>

height  = 69;         // overall height above the drawer floor (mm); the drawer is 69mm tall
wall_t  = 1.6;        // wall thickness (mm)
floor_t = 1.6;        // floor thickness above the base pads (mm)

long_diag_container_slice(3, 10, height, wall_t, floor_t, fnx = long_left_flare(height), side = -1, cx = long_span_x(long_left_cols), c0 = 5, c1 = 10);
