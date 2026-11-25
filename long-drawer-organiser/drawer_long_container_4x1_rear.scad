// Long Drawer Organiser — three-sided 4 x 1 rear container behind the narrow slots
// Render this file to generate drawer_long_container_4x1_rear.stl
// 167.5 x 41.5mm floor with full base pads (row 10, columns 7-10), printable whole. Print ONE.
// Keeps both long walls (-Y against the 2 x 8 slots, +Y against the drawer back) and the +X short
// wall; seated turned 180 degrees, the +X wall goes against the wide container and the open short
// side faces the drawer's right wall.
// open_right flips which short side of the part is open; irrelevant to the drawer when seated rotated 180.
// No rotate(): sources stay OpenSCAD Z-up; the viewer applies the Z-up -> Y-up conversion itself.

include <_drawer_long.scad>

height  = 69;         // overall height above the drawer floor (mm); the drawer is 69mm tall
wall_t  = 1.6;        // wall thickness (mm)
floor_t = 1.6;        // floor thickness above the base pads (mm)
open_right = false;   // true opens the +X short side instead of -X

long_open_container(4, 1, height, wall_t, floor_t, open_nx = !open_right, open_px = open_right);
