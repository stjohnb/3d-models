// Drawer Organiser — back piece of the left container (3 x 10 cells)
// Render this file to generate drawer_container_left_back.stl
// 144.25 x 209.75mm — cells [5,10) of the container's 10-cell depth, split at
// the baseplate tile seam underneath (issue #319). This split deliberately
// stays on the tile seam — issue #322 offsets the other containers' seams,
// but a 10-cell depth only makes two <=5-cell pieces by cutting at 5, and two
// pieces were preferred over three. Print together with
// drawer_container_left_front to assemble the full 126 x 420 x 69mm left
// container; the two pieces are mirror images, not the same part.
//
// Seat both pieces on a baseplate first — the pads and sockets are the
// alignment jig — then glue the flat faces with CA.
//
// Stands against the drawer's left wall, so its -X wall leans outward with
// height to follow the drawer (see side_flare() in _drawer_organiser.scad).
// No rotate(): sources stay OpenSCAD Z-up; the viewer applies the Z-up -> Y-up conversion itself.

include <_drawer_organiser.scad>

grid_x  = 3;          // cells across (X) of the ASSEMBLED container
grid_y  = 10;         // cells deep (Y) of the ASSEMBLED container
height  = 69;         // overall height above the drawer floor (mm); the drawer is 69mm tall
wall_t  = 1.6;        // wall thickness (mm)
floor_t = 1.6;        // floor thickness above the base pads (mm)

container_slice(grid_x, grid_y, height, wall_t, floor_t,
                fnx = side_flare(height),
                split_y = true, c0 = 5, c1 = 10);
