// Drawer Organiser — left container of the full-drawer layout (3 x 10 cells)
// Render this file to generate drawer_container_left.stl
// 126 x 420 x 69mm assembled — too long for an A1's 250mm bed. This file
// renders the whole container; the printable pieces ship as
// drawer_container_left_front / drawer_container_left_back, split at the
// baseplate tile seam underneath (issue #319). Its pieces stay split on the
// seam — a 10-cell depth only makes two <=5-cell pieces by cutting at 5, and
// two pieces were preferred over three (issue #322). The customizer
// split_parts/part_index remain for other bed sizes.
//
// Stands against the drawer's left wall, so its -X wall leans outward with
// height to follow the drawer (see side_flare() in _drawer_organiser.scad).
// No rotate(): sources stay OpenSCAD Z-up; the viewer applies the Z-up -> Y-up conversion itself.

include <_drawer_organiser.scad>

grid_x  = 3;          // cells across (X)
grid_y  = 10;         // cells deep (Y)
height  = 69;         // overall height above the drawer floor (mm); the drawer is 69mm tall
wall_t  = 1.6;        // wall thickness (mm)
floor_t = 1.6;        // floor thickness above the base pads (mm)
split_parts = 1;      // pieces to split into along Y for the print bed
part_index  = 0;      // which piece this render returns

container_part(grid_x, grid_y, height, wall_t, floor_t,
               fnx = side_flare(height),
               split_y = true, parts = split_parts, index = part_index);
