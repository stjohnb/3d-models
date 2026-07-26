// Drawer Organiser — front piece of the left container (3 x 10 cells)
// Render this file to generate drawer_container_left_front.stl
// 138.45 x 209.75mm — cells [0,5) of the container's 10-cell depth, split at
// the baseplate tile seam underneath (issue #319). This split deliberately
// stays on the tile seam — issue #322 offsets the other containers' seams,
// but a 10-cell depth only makes two <=5-cell pieces by cutting at 5, and two
// pieces were preferred over three. Print together with
// drawer_container_left_back to assemble the full 126 x 420 x 56mm left
// container; the two pieces are mirror images, not the same part.
//
// Seat both pieces on a baseplate first — the pads and sockets are the
// alignment jig — then glue the flat faces with CA.
//
// Stands against the drawer's left wall, so its -X wall leans outward with
// height to follow the drawer (see side_flare() in _drawer_organiser.scad).
// No rotate(): the project sets viewer_rotate_x in meta.json.

include <_drawer_organiser.scad>

grid_x  = 3;          // cells across (X) of the ASSEMBLED container
grid_y  = 10;         // cells deep (Y) of the ASSEMBLED container
z_units = 8;          // 7mm height units -> 56mm tall
wall_t  = 1.6;        // wall thickness (mm)
floor_t = 1.6;        // floor thickness above the base pads (mm)

container_slice(grid_x, grid_y, z_units, wall_t, floor_t,
                fnx = side_flare(z_units),
                split_y = true, c0 = 0, c1 = 5);
