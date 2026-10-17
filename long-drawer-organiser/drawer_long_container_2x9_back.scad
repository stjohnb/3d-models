// Long Drawer Organiser — back four cells of a narrow 2 x 9 slot
// Render this file to generate drawer_long_container_2x9_back.stl
// 83.5 x 167.75mm — rows 7-10 of the slot, closed back, open front. Print TWO; glue to the printed drawer_long_container_2x10_half.
// No rotate(): sources stay OpenSCAD Z-up; the viewer applies the Z-up -> Y-up conversion itself.

include <_drawer_long.scad>

height  = 69;         // overall height above the drawer floor (mm); the drawer is 69mm tall
wall_t  = 1.6;        // wall thickness (mm)
floor_t = 1.6;        // floor thickness above the base pads (mm)

container_slice(2, 9, height, wall_t, floor_t, split_y = true, c0 = 5, c1 = 9);
