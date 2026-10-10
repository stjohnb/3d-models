// Drawer Organiser — narrow front container of the full-drawer layout (1 x 3 cells)
// Render this file to generate drawer_container_front_1x3.stl
// 42 x 126 x 69mm assembled — 41.5 x 125.5mm at the floor, ~60.25mm wide at the
// rim where the flared wall leans out. It FITS an A1's 250mm bed, so the whole
// file is the printable part and there are no piece files. The customizer
// split_parts/part_index are retained for smaller beds.
//
// Occupies the front of the drawer's last column (issue #324), standing against
// the right wall, so its +X wall leans outward with height to follow the drawer
// (see side_flare() in _drawer_organiser.scad). The single cell behind it is
// drawer_container_front_1x1.
// No rotate(): sources stay OpenSCAD Z-up; the viewer applies the Z-up -> Y-up conversion itself.

include <_drawer_organiser.scad>

grid_x  = 1;          // cells across (X)
grid_y  = 3;          // cells deep (Y)
height  = 69;         // overall height above the drawer floor (mm); the drawer is 69mm tall
wall_t  = 1.6;        // wall thickness (mm)
floor_t = 1.6;        // floor thickness above the base pads (mm)
split_parts = 1;      // pieces to split into along Y for the print bed
part_index  = 0;      // which piece this render returns

container_part(grid_x, grid_y, height, wall_t, floor_t,
               fpx = side_flare(height),
               split_y = true, parts = split_parts, index = part_index);
