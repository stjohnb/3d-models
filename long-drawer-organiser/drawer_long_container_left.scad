// Long Drawer Organiser — flared left container of the diagonal wide pair (whole, viewing aid)
// Render this file to generate drawer_long_container_left.stl
// Columns 1-3 at the front narrowing to 1-2 at the rear along the diagonal. Print the _front and _back pieces.
// No rotate(): sources stay OpenSCAD Z-up; the viewer applies the Z-up -> Y-up conversion itself.

include <_drawer_long.scad>

height  = 69;         // overall height above the drawer floor (mm); the drawer is 69mm tall
wall_t  = 1.6;        // wall thickness (mm)
floor_t = 1.6;        // floor thickness above the base pads (mm)

long_diag_container(3, 10, height, wall_t, floor_t, fnx = long_left_flare(height), side = -1, cx = long_span_x(long_left_cols));
