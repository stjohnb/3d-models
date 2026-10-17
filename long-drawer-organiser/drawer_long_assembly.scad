// Long Drawer Organiser — assembly preview
// Render this file to generate drawer_long_assembly.stl.
//
// A viewing aid, not a printable part: the 10 x 10 baseplate floor (two
// drawer_baseplate_5x5 in front, two _back behind) as one slab, and five
// containers seated on top: a flared left container and an unflared one split by
// a continuous diagonal (3 + 3 cells at the front, 2 + 4 at the rear), two 2 x 9
// narrow slots against the vertical right wall and a 4 x 1 across their front.
// See layout.md.
// Colours are from filament-colors.json.
// No rotate(): sources stay OpenSCAD Z-up; the viewer applies the Z-up -> Y-up conversion itself.

include <_drawer_long.scad>

grid_x  = long_drawer_grid_x;
grid_y  = long_drawer_grid_y;
height  = long_drawer_height;
wall_t  = 1.6;
floor_t = 1.6;
flare   = long_left_flare(height);

narrow_y = long_span_y(long_narrow_rows);

color("#9e9e9e") baseplate(grid_x, grid_y);   // Grey
color("#64b5f6") translate([long_span_x(long_left_cols), 0, 0])
    long_diag_container(3, grid_y, height, wall_t, floor_t, fnx = flare, side = -1, cx = long_span_x(long_left_cols));   // Blue
color("#43a047") translate([long_span_x(long_centre_cols), 0, 0])
    long_diag_container(4, grid_y, height, wall_t, floor_t, side = 1, cx = long_span_x(long_centre_cols));                // Green
color("#e53935") translate([long_span_x(long_narrow_a_cols), narrow_y, 0]) container(2, 9, height, wall_t, floor_t);      // Red
color("#fdd835") translate([long_span_x(long_narrow_b_cols), narrow_y, 0]) container(2, 9, height, wall_t, floor_t);      // Yellow
color("#fb8c00") translate([long_span_x(long_front_cols), long_row_y(long_front_row), 0]) container(4, 1, height, wall_t, floor_t);  // Orange
