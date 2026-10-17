// Long Drawer Organiser — second drawer (long implements)
// Library: the long-implement drawer's dimensions on top of the drawer-organiser
// project's _drawer_organiser.scad, shared by cross-project include, not copied.
// Issues clw_01M43Z7AXXMZQCK6ZDVCBB6K4D and clw_01M4R6ED006HYSY6F15NMYHMGD; see layout.md.
//   422mm floor width: measured by fitting two 5 × 5 tiles after widening the
//   drawer with an adjustable knife holder (420mm grid + 2mm fit slack).
//   425mm front to back.
//   LEFT wall flares like the first drawer (20mm over 69mm); RIGHT wall is vertical.
//   Height not remeasured — the first drawer's 69mm is assumed.
// The 10 x 10 grid sits flush to the LEFT wall at the floor, so the taper relative
// to the grid edge is exactly the first drawer's and drawer_container_left_front /
// _back fit unchanged. The 2mm width slack goes RIGHT, against the vertical wall.

include <../drawer-organiser/_drawer_organiser.scad>

long_drawer_grid_x   = 10;    // two 5 x 5 tiles across
long_drawer_grid_y   = 10;    // floor(425 / 42)
long_drawer_slack    = 2;     // fit slack against the vertical right wall
long_drawer_floor_w  = long_drawer_grid_x * cell_pitch + long_drawer_slack;  // 422; measured by fitting two 5 × 5 tiles after widening the drawer with an adjustable knife holder
long_drawer_depth    = 425;   // front to back
long_drawer_height   = drawer_height;                        // 69, assumed
long_drawer_taper    = (drawer_top_w - drawer_bottom_w) / 2; // 20, LEFT wall only

// Outward top offset for a container against the LEFT wall: wall leans out
// long_drawer_taper over long_drawer_height, the outer face starts 0.25mm
// inboard of the grid edge, the rim stops container_wall_clear short. 18.75mm
// at h = 69 — the same as side_flare(69).
function long_left_flare(h) =
    long_drawer_taper * h / long_drawer_height
    - container_wall_clear + (4 - pad_r_top);

assert(abs(long_left_flare(drawer_height) - side_flare(drawer_height)) < 1e-9,
       "long_left_flare must match side_flare so the existing left container pieces fit");

// === Layout (see layout.md) === 0-based columns/rows, grid centred, front = -Y
long_left_cols     = [0, 2];   long_centre_cols = [2, 5];
long_narrow_a_cols = [6, 7];   long_narrow_b_cols = [8, 9];
long_narrow_rows   = [1, 9];   long_front_cols = [6, 9];   long_front_row = 0;
function long_col_x(i)  = (i - (long_drawer_grid_x - 1) / 2) * cell_pitch;
function long_row_y(j)  = (j - (long_drawer_grid_y - 1) / 2) * cell_pitch;
function long_span_x(c) = (long_col_x(c[0]) + long_col_x(c[1])) / 2;
function long_span_y(r) = (long_row_y(r[0]) + long_row_y(r[1])) / 2;

// === Diagonal boundary of the wide pair ===
long_grid_w = long_drawer_grid_x * cell_pitch;  long_grid_d = long_drawer_grid_y * cell_pitch;
long_diag_front_edge = 3;  long_diag_rear_edge = 2;   // column boundary at front / rear edge
long_diag_x_front = -long_grid_w / 2 + long_diag_front_edge * cell_pitch;   // -84
long_diag_x_rear  = -long_grid_w / 2 + long_diag_rear_edge  * cell_pitch;   // -126
function long_diag_x(y) = long_diag_x_front
    + (long_diag_x_rear - long_diag_x_front) * (y + long_grid_d / 2) / long_grid_d;
long_diag_angle = atan((long_diag_x_front - long_diag_x_rear) / long_grid_d);  // 5.71 deg
long_edge_inset = 4 - pad_r_top;                          // 0.25
long_diag_inset = long_edge_inset / cos(long_diag_angle);  // same clearance along X

// gx x gy container() clipped to one side of the diagonal and closed with a wall.
// cx = the footprint's centre x in grid coords; side = -1 keeps -X, +1 keeps +X.
// Must span the full grid depth (centred on y = 0).
module long_diag_container(gx, gy, h, wall_t, floor_t, fnx = 0, side = -1, cx = 0) {
    ox = gx * cell_pitch / 2 - 4;  oy = gy * cell_pitch / 2 - 4;  big = 500;
    xo_lo = long_diag_x(-big) - cx + side * long_diag_inset;   // outer face at y = -big
    xo_hi = long_diag_x( big) - cx + side * long_diag_inset;
    wt    = wall_t / cos(long_diag_angle);
    xi_lo = xo_lo + side * wt;  xi_hi = xo_hi + side * wt;     // inner face
    far   = side * big;
    union() {
        intersection() {
            container(gx, gy, h, wall_t, floor_t, fnx = fnx);
            translate([0, 0, -1]) linear_extrude(h + 2)
                polygon([[xo_lo, -big], [xo_hi, big], [far, big], [far, -big]]);
        }
        intersection() {   // the wall: starts at pad_height, buried in the floor slab
            container_shell(ox, oy, pad_r_top, pad_height, h, fnx, 0, 0, 0, pad_height, h);
            translate([0, 0, pad_height]) linear_extrude(h - pad_height)
                polygon([[xo_lo, -big], [xo_hi, big], [xi_hi, big], [xi_lo, -big]]);
        }
    }
}

// Rows [c0, c1) of a long_diag_container, re-centred; same keep-box rules as container_slice().
module long_diag_container_slice(gx, gy, h, wall_t, floor_t, fnx = 0, side = -1, cx = 0,
                                 c0 = 0, c1 = undef) {
    n = gy;  b1 = is_undef(c1) ? n : c1;
    assert(c0 >= 0 && b1 <= n && b1 > c0, "long_diag_container_slice: need 0 <= c0 < c1 <= gy");
    L = n * cell_pitch;  big = 500;
    lo = -L / 2 + c0 * cell_pitch;  hi = -L / 2 + b1 * cell_pitch;
    klo = (c0 == 0) ? lo - big : lo;  khi = (b1 == n) ? hi + big : hi;  mid = (lo + hi) / 2;
    translate([0, -mid, 0]) intersection() {
        long_diag_container(gx, gy, h, wall_t, floor_t, fnx, side, cx);
        translate([-big, klo, -1]) cube([2 * big, khi - klo, h + 2]);
    }
}
