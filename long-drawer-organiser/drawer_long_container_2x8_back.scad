// Long Drawer Organiser — back three cells of a narrow 2 x 8 slot
// Render this file to generate drawer_long_container_2x8_back.stl
// 83.5 x 125.75mm — rows 7-9 of the grid (cells 5-7 of the slot), closed back, open front. Print TWO; glue each to a printed drawer_long_container_2x10_half.
// No rotate(): sources stay OpenSCAD Z-up; the viewer applies the Z-up -> Y-up conversion itself.

include <_drawer_long.scad>

height  = 69;         // overall height above the drawer floor (mm); the drawer is 69mm tall
wall_t  = 1.6;        // wall thickness (mm)
floor_t = 1.6;        // floor thickness above the base pads (mm)

container_slice(2, 8, height, wall_t, floor_t, split_y = true, c0 = 5, c1 = 8);
