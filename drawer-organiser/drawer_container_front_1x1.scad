// Drawer Organiser — single-cell front container of the full-drawer layout (1 x 1 cell)
// Render this file to generate drawer_container_front_1x1.stl
// 42 x 42 x 69mm assembled — 41.5 x 41.5mm at the floor, ~60.25mm wide at the
// rim where the flared wall leans out. Comfortably inside an A1's 250mm bed, so
// the whole file is the printable part. A single cell cannot be split at all,
// so unlike the other containers this file exposes no split_parts/part_index
// and calls container() directly.
//
// Fills the last cell of the drawer's last column, behind
// drawer_container_front_1x3 (issue #324). Stands against the right wall, so
// its +X wall leans outward with height to follow the drawer (see side_flare()
// in _drawer_organiser.scad).
// No rotate(): the project sets viewer_rotate_x in meta.json.

include <_drawer_organiser.scad>

grid_x  = 1;          // cells across (X)
grid_y  = 1;          // cells deep (Y)
height  = 69;         // overall height above the drawer floor (mm); the drawer is 69mm tall
wall_t  = 1.6;        // wall thickness (mm)
floor_t = 1.6;        // floor thickness above the base pads (mm)

container(grid_x, grid_y, height, wall_t, floor_t,
          fpx = side_flare(height));
