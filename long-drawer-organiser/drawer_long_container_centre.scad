// Long Drawer Organiser — unflared diagonal container, 3 wide at front to 4 wide at rear (whole, viewing aid)
// Render this file to generate drawer_long_container_centre.stl
// Print the _front and _back pieces.
// No rotate(): sources stay OpenSCAD Z-up; the viewer applies the Z-up -> Y-up conversion itself.

include <_drawer_long.scad>

height  = 69;         // overall height above the drawer floor (mm); the drawer is 69mm tall
wall_t  = 1.6;        // wall thickness (mm)
floor_t = 1.6;        // floor thickness above the base pads (mm)

long_diag_container(4, 10, height, wall_t, floor_t, side = 1, cx = long_span_x(long_centre_cols));
