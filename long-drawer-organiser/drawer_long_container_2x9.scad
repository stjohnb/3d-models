// Long Drawer Organiser — narrow full-depth slot of the long-implement drawer (2 x 9 cells)
// Render this file to generate drawer_long_container_2x9.stl
// 84 x 378 x 69mm nominal (83.5 x 377.5 actual). Serves both narrow
// slots (spatulas, whisks, spoons, tongs). The printable piece is
// drawer_long_container_2x10_half plus drawer_long_container_2x9_back; this file renders the whole container, and
// the customizer split_parts/part_index remain for other bed sizes.
// No rotate(): sources stay OpenSCAD Z-up; the viewer applies the Z-up -> Y-up conversion itself.

include <_drawer_long.scad>

grid_x  = 2;          // cells across (X)
grid_y  = 9;          // cells deep (Y)
height  = 69;         // overall height above the drawer floor (mm); the drawer is 69mm tall
wall_t  = 1.6;        // wall thickness (mm)
floor_t = 1.6;        // floor thickness above the base pads (mm)
split_parts = 1;      // pieces to split into along Y for the print bed
part_index  = 0;      // which piece this render returns

container_part(grid_x, grid_y, height, wall_t, floor_t,
               split_y = true, parts = split_parts, index = part_index);
