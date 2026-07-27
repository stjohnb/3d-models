// Drawer Organiser — middle front container of the full-drawer layout (3 x 4 cells)
// Render this file to generate drawer_container_front_3x4.stl
// 126 x 168 x 69mm assembled (125.5 x 167.5mm actual) — this one FITS an A1's
// 250mm bed, so the whole file is the printable part and there are no piece
// files. The customizer split_parts/part_index are retained for smaller beds.
//
// Issue #324's text calls this container "3x3", but the sketch draws it the
// full 4 rows deep, level with the 8 x 4 beside it, and only 3 x 4 tiles the
// 15 x 10 grid exactly (3 x 3 would leave a 3 x 1 hole). Implemented as 3 x 4
// — see layout.md, "Container layout".
//
// Sits away from both drawer walls, so no wall flares.
// No rotate(): the project sets viewer_rotate_x in meta.json.

include <_drawer_organiser.scad>

grid_x  = 3;          // cells across (X)
grid_y  = 4;          // cells deep (Y)
height  = 69;         // overall height above the drawer floor (mm); the drawer is 69mm tall
wall_t  = 1.6;        // wall thickness (mm)
floor_t = 1.6;        // floor thickness above the base pads (mm)
split_parts = 1;      // pieces to split into along Y for the print bed
part_index  = 0;      // which piece this render returns

container_part(grid_x, grid_y, height, wall_t, floor_t,
               split_y = true, parts = split_parts, index = part_index);
