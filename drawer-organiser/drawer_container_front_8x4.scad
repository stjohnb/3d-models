// Drawer Organiser — wide front container of the full-drawer layout (8 x 4 cells)
// Render this file to generate drawer_container_front_8x4.stl
// 336 x 168 x 69mm assembled — far too wide for an A1's 250mm bed. This file
// renders the whole container; the printable pieces ship as
// drawer_container_front_8x4_half (x2), split along X offset from the
// baseplate tile seams underneath so each half straddles a grid join
// (issue #322). The customizer split_parts/part_index remain for other bed
// sizes.
//
// Sits in the front row, away from both drawer walls, so no wall flares.
// No rotate(): the project sets viewer_rotate_x in meta.json.

include <_drawer_organiser.scad>

grid_x  = 8;          // cells across (X)
grid_y  = 4;          // cells deep (Y)
height  = 69;         // overall height above the drawer floor (mm); the drawer is 69mm tall
wall_t  = 1.6;        // wall thickness (mm)
floor_t = 1.6;        // floor thickness above the base pads (mm)
split_parts = 1;      // pieces to split into along X for the print bed
part_index  = 0;      // which piece this render returns

container_part(grid_x, grid_y, height, wall_t, floor_t,
               split_y = false, parts = split_parts, index = part_index);
