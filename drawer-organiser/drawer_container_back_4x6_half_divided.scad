// Drawer Organiser — half of an unflared back-row container (4 x 6 cells),
// with five upright dividers
// Render this file to generate drawer_container_back_4x6_half_divided.stl
// Same shell as drawer_container_back_4x6_half (167.5 x 125.75mm, cells [0,3)
// of the container's 6-cell depth, cut at rows 7|8 offset from the baseplate
// tile seam — issues #319/#322), plus five plates across the interior width
// that split it into six equal segments to stop items falling over.
//
// The plates are 3/4 of the container height (51.75mm above the drawer floor)
// and run half the piece's interior depth, centred, so the front and back
// quarters of the piece stay clear. They touch nothing but the floor, so the
// footprint, rim and baseplate fit are identical to the undivided half — the
// two parts are interchangeable on the same baseplate.
//
// Still 180-degree rotationally symmetric as a printed piece: print two per
// container, rotating one 180 degrees about Z. The assembled container then
// has two banks of five dividers, one in each half, aligned across the width.
//
// Seat the pieces on the assembled baseplate first — the pads and sockets are
// the alignment jig — then glue the flat faces with CA.
// No rotate(): the project sets viewer_rotate_x in meta.json.

include <_drawer_organiser.scad>

grid_x    = 4;          // cells across (X) of the ASSEMBLED container
grid_y    = 6;          // cells deep (Y) of the ASSEMBLED container
height    = 69;         // overall height above the drawer floor (mm)
wall_t    = 1.6;        // wall thickness (mm); also the divider thickness
floor_t   = 1.6;        // floor thickness above the base pads (mm)
div_count = 5;          // dividers; div_count + 1 equal segments across the width

union() {
    container_slice(grid_x, grid_y, height, wall_t, floor_t,
                    split_y = true, c0 = 0, c1 = 3);
    container_dividers(grid_x, grid_y, height, wall_t, floor_t,
                       split_y = true, c0 = 0, c1 = 3,
                       count = div_count, h_frac = 0.75, len_frac = 0.5);
}
