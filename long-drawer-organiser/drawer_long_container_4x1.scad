// Long Drawer Organiser — three-sided 4 x 1 front container across the narrow slots
// Render this file to generate drawer_long_container_4x1.stl
// 167.5 x 41.5mm floor with full base pads, printable whole. Print ONE.
// Seated turned 180 degrees: the kept +Y long wall goes against the drawer front and the kept +X short
// wall against the wide container; the dropped -Y and -X sides face the 2 x 8 slots and the drawer's right wall.
// No rotate(): sources stay OpenSCAD Z-up; the viewer applies the Z-up -> Y-up conversion itself.

include <_drawer_long.scad>

height  = 69;         // overall height above the drawer floor (mm); the drawer is 69mm tall
wall_t  = 1.6;        // wall thickness (mm)
floor_t = 1.6;        // floor thickness above the base pads (mm)

long_open_container(4, 1, height, wall_t, floor_t, open_nx = true, open_ny = true);
