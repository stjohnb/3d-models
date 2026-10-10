// Drawer Organiser — long-implement drawer assembly preview
// Render this file to generate drawer_long_assembly.stl.
//
// A viewing aid, not a printable part: the 9 x 10 baseplate floor as one slab
// with the right-hand filler strip, and four full-depth containers (front to
// back along Y) seated on top: a 3-wide flared container against the flared
// left wall, then three narrow 2-wide slots. See layout.md "Second drawer:
// long implements". Colours are from filament-colors.json.
// No rotate(): sources stay OpenSCAD Z-up; the viewer applies the Z-up -> Y-up conversion itself.

include <_drawer_long.scad>

grid_x  = long_drawer_grid_x;
grid_y  = long_drawer_grid_y;
height  = long_drawer_height;
wall_t  = 1.6;
floor_t = 1.6;
flare   = long_left_flare(height);

function cx(i) = (i - (grid_x - 1) / 2) * cell_pitch;   // x of column i (0-based)
function cy(j) = (j - (grid_y - 1) / 2) * cell_pitch;   // y of row j    (0-based)
function span_c(a, b) = (cx(a) + cx(b)) / 2;            // centre x of columns a..b
function span_r(a, b) = (cy(a) + cy(b)) / 2;            // centre y of rows a..b

color("#9e9e9e") baseplate(grid_x, grid_y);   // Grey
color("#9e9e9e")   // overlaps the slab by eps: no coincident face for CGAL
    translate([grid_x * cell_pitch / 2 + long_drawer_fill_w / 2 - eps, 0, 0])
        filler(grid_y, long_drawer_fill_w);
color("#64b5f6") translate([span_c(0, 2), span_r(0, 9), 0]) container(3, 10, height, wall_t, floor_t, fnx = flare);  // Blue
color("#43a047") translate([span_c(3, 4), span_r(0, 9), 0]) container(2, 10, height, wall_t, floor_t);               // Green
color("#e53935") translate([span_c(5, 6), span_r(0, 9), 0]) container(2, 10, height, wall_t, floor_t);               // Red
color("#fdd835") translate([span_c(7, 8), span_r(0, 9), 0]) container(2, 10, height, wall_t, floor_t);               // Yellow
