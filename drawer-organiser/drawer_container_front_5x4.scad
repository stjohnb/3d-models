// Drawer Organiser — wide front container of the full-drawer layout (5 x 4 cells)
// Render this file to generate drawer_container_front_5x4.stl
// 210 x 168 x 69mm assembled (209.5 x 167.5mm actual) — this one FITS an A1's
// 250mm bed, so the whole file is the printable part and there are no piece
// files. Replaces the former 8 x 4 wide front container, split 5 + 3 per
// issue #334.
//
// Sits in the front row, away from both drawer walls, so no wall flares.
// No rotate(): sources stay OpenSCAD Z-up; the viewer applies the Z-up -> Y-up conversion itself.

include <_drawer_organiser.scad>

grid_x  = 5;          // cells across (X)
grid_y  = 4;          // cells deep (Y)
height  = 69;         // overall height above the drawer floor (mm); the drawer is 69mm tall
wall_t  = 1.6;        // wall thickness (mm)
floor_t = 1.6;        // floor thickness above the base pads (mm)
split_parts = 1;      // pieces to split into along X for the print bed
part_index  = 0;      // which piece this render returns

container_part(grid_x, grid_y, height, wall_t, floor_t,
               split_y = false, parts = split_parts, index = part_index);
