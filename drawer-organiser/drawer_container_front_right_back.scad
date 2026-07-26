// Drawer Organiser — back piece of the front-right container (4 x 7 cells)
// Render this file to generate drawer_container_front_right_back.stl
// 180.45 x 167.75mm — cells [3,7) of the container's 7-cell depth, split
// offset from the baseplate tile seam so a solid piece straddles the grid
// join and the cut faces meet mid-tile (issue #322). Print together with
// drawer_container_front_right_front to assemble the full 168 x 294 x 56mm
// front-right container.
//
// Stands against the drawer's right wall, so its +X wall leans outward with
// height to follow the drawer (see side_flare() in _drawer_organiser.scad).
// Seat both pieces on the assembled baseplate first — the pads and sockets
// are the alignment jig — then glue the flat faces with CA.
// No rotate(): the project sets viewer_rotate_x in meta.json.

include <_drawer_organiser.scad>

grid_x  = 4;          // cells across (X) of the ASSEMBLED container
grid_y  = 7;          // cells deep (Y) of the ASSEMBLED container
z_units = 8;          // 7mm height units -> 56mm tall
wall_t  = 1.6;        // wall thickness (mm)
floor_t = 1.6;        // floor thickness above the base pads (mm)

container_slice(grid_x, grid_y, z_units, wall_t, floor_t,
                fpx = side_flare(z_units),
                split_y = true, c0 = 3, c1 = 7);
