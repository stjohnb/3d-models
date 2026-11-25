// Long Drawer Organiser — half (five cells) of the unflared 4 x 10 container
// Render this file to generate drawer_long_container_centre_4x10_half.stl
// 167.5 x 209.75mm. 180-degree symmetric, so both halves are this part: print TWO
// and rotate one 180 degrees about Z when gluing.
// No rotate(): sources stay OpenSCAD Z-up; the viewer applies the Z-up -> Y-up conversion itself.

include <_drawer_long.scad>

height  = 69;         // overall height above the drawer floor (mm); the drawer is 69mm tall
wall_t  = 1.6;        // wall thickness (mm)
floor_t = 1.6;        // floor thickness above the base pads (mm)

container_slice(4, 10, height, wall_t, floor_t, split_y = true, c0 = 0, c1 = 5);
