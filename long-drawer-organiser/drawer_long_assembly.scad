// Long Drawer Organiser — assembly preview
// Render this file to generate drawer_long_assembly.stl.
//
// A viewing aid, not a printable part: the 10 x 10 baseplate floor (two
// drawer_baseplate_5x5 in front, two _back behind) as one slab, and six
// containers seated on top: a flared 2 x 10 (columns 1-2) and an unflared 4 x 10
// (columns 3-6), two 2 x 8 narrow slots (rows 2-9) against the vertical right
// wall, a three-sided 4 x 1 across their front (row 1, walled at the drawer front and against the 4 x 10,
// open on +X and +Y) and a 4 x 1 behind them (row 10) open on its +X short side. Both 4 x 1 are the
// printed parts seated turned 180 degrees. See layout.md.
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
narrow_gy = long_narrow_rows[1] - long_narrow_rows[0] + 1;

color("#9e9e9e") baseplate(grid_x, grid_y);   // Grey
color("#64b5f6") translate([long_span_x(long_left_cols), 0, 0])
    container(2, grid_y, height, wall_t, floor_t, fnx = flare);   // Blue
color("#43a047") translate([long_span_x(long_centre_cols), 0, 0])
    container(4, grid_y, height, wall_t, floor_t);                // Green
color("#e53935") translate([long_span_x(long_narrow_a_cols), narrow_y, 0]) container(2, narrow_gy, height, wall_t, floor_t);      // Red
color("#fdd835") translate([long_span_x(long_narrow_b_cols), narrow_y, 0]) container(2, narrow_gy, height, wall_t, floor_t);      // Yellow
// Both 4 x 1 are the printed parts seated turned 180 degrees about their own centre, so their open short sides face +X.
color("#fb8c00") translate([long_span_x(long_front_cols), long_row_y(long_front_row), 0]) rotate([0, 0, 180]) long_open_container(4, 1, height, wall_t, floor_t, open_nx = true, open_ny = true);  // Orange
color("#f5f5f5") translate([long_span_x(long_front_cols), long_row_y(long_rear_row), 0]) rotate([0, 0, 180]) long_open_container(4, 1, height, wall_t, floor_t, open_nx = true);  // White
