// Drawer Organiser — back piece of the back-right container (4 x 6 cells)
// Render this file to generate drawer_container_back_4x6_right_back.stl
// 186.25 x 125.75mm — cells [3,6) of the container's 6-cell depth, cut at
// cell 3 (rows 7|8 of the drawer, 1-based) so the cut face meets its partner
// over the middle of the back baseplate tile (issues #319/#322). Print together
// with drawer_container_back_4x6_right_front to assemble the full
// 168 x 252 x 69mm back-right container.
//
// Stands against the drawer's right wall, so its +X wall leans outward with
// height to follow the drawer (see side_flare() in _drawer_organiser.scad).
// The flare is what makes these two pieces mirror images rather than the same
// part: rotating one 180 degrees about Z to serve as the other would put the
// leaning wall on the wrong side. Print one of each. (The unflared back-row
// containers do not have this problem — see drawer_container_back_4x6_half.)
//
// Seat both pieces on the assembled baseplate first — the pads and sockets are
// the alignment jig — then glue the flat faces with CA.
// No rotate(): the project sets viewer_rotate_x in meta.json.

include <_drawer_organiser.scad>

grid_x  = 4;          // cells across (X) of the ASSEMBLED container
grid_y  = 6;          // cells deep (Y) of the ASSEMBLED container
height  = 69;         // overall height above the drawer floor (mm); the drawer is 69mm tall
wall_t  = 1.6;        // wall thickness (mm)
floor_t = 1.6;        // floor thickness above the base pads (mm)

container_slice(grid_x, grid_y, height, wall_t, floor_t,
                fpx = side_flare(height),
                split_y = true, c0 = 3, c1 = 6);
