// Long Drawer Organiser — unflared 4 x 10 container, columns 3-6 (whole, viewing aid)
// Render this file to generate drawer_long_container_centre_4x10.stl
// Unflared 4 x 10 of the wide pair. Print two _centre_4x10_half pieces.
// No rotate(): sources stay OpenSCAD Z-up; the viewer applies the Z-up -> Y-up conversion itself.

include <_drawer_long.scad>

height  = 69;         // overall height above the drawer floor (mm); the drawer is 69mm tall
wall_t  = 1.6;        // wall thickness (mm)
floor_t = 1.6;        // floor thickness above the base pads (mm)

container(4, 10, height, wall_t, floor_t);
