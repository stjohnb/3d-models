// Long Drawer Organiser — flared 2 x 10 container, columns 1-2 (whole, viewing aid)
// Render this file to generate drawer_long_container_left_2x10.stl
// Flared 2 x 10 of the wide pair. Print the _front and _back pieces.
// No rotate(): sources stay OpenSCAD Z-up; the viewer applies the Z-up -> Y-up conversion itself.

include <_drawer_long.scad>

height  = 69;         // overall height above the drawer floor (mm); the drawer is 69mm tall
wall_t  = 1.6;        // wall thickness (mm)
floor_t = 1.6;        // floor thickness above the base pads (mm)

container(2, 10, height, wall_t, floor_t, fnx = long_left_flare(height));
