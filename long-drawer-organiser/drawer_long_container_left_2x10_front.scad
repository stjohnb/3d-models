// Long Drawer Organiser — front five cells of the flared 2 x 10 container
// Render this file to generate drawer_long_container_left_2x10_front.stl
// 83.5 x 209.75mm at the floor, about 102.25mm wide at the rim. Print ONE; glue to _left_2x10_back.
// The flare breaks 180-degree symmetry: front and back are mirror images, not the same part.
// No rotate(): sources stay OpenSCAD Z-up; the viewer applies the Z-up -> Y-up conversion itself.

include <_drawer_long.scad>

height  = 69;         // overall height above the drawer floor (mm); the drawer is 69mm tall
wall_t  = 1.6;        // wall thickness (mm)
floor_t = 1.6;        // floor thickness above the base pads (mm)

container_slice(2, 10, height, wall_t, floor_t, fnx = long_left_flare(height), split_y = true, c0 = 0, c1 = 5);
