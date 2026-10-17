// Long Drawer Organiser — 4 x 1 front container across the narrow slots
// Render this file to generate drawer_long_container_4x1.stl
// 167.5 x 41.5mm, printable whole. Print ONE.
// No rotate(): sources stay OpenSCAD Z-up; the viewer applies the Z-up -> Y-up conversion itself.

include <_drawer_long.scad>

height  = 69;         // overall height above the drawer floor (mm); the drawer is 69mm tall
wall_t  = 1.6;        // wall thickness (mm)
floor_t = 1.6;        // floor thickness above the base pads (mm)

container(4, 1, height, wall_t, floor_t);
