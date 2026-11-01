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
// to the grid edge is exactly the first drawer's. The 2mm width slack goes RIGHT, against the vertical wall.

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
       "long_left_flare must match side_flare so the flared container matches the first drawer");

// === Layout (see layout.md) === 0-based columns/rows, grid centred, front = -Y
long_left_cols     = [0, 1];   long_centre_cols = [2, 5];
long_narrow_a_cols = [6, 7];   long_narrow_b_cols = [8, 9];
long_narrow_rows   = [1, 8];   long_front_cols = [6, 9];   long_front_row = 0;
long_rear_row      = 9;
function long_col_x(i)  = (i - (long_drawer_grid_x - 1) / 2) * cell_pitch;
function long_row_y(j)  = (j - (long_drawer_grid_y - 1) / 2) * cell_pitch;
function long_span_x(c) = (long_col_x(c[0]) + long_col_x(c[1])) / 2;
function long_span_y(r) = (long_row_y(r[0]) + long_row_y(r[1])) / 2;

// container() with chosen walls dropped above the floor slab, for a piece whose
// neighbours close the compartment. The floor slab and base pads keep the full
// footprint, so the piece still seats on the baseplate. Each dropped wall is cut
// back to its corner-arc centre line, so the kept walls end in flat faces.
module long_open_container(gx, gy, h, wall_t, floor_t,
                           open_nx = false, open_px = false, open_ny = false, open_py = false) {
    ox = gx * cell_pitch / 2 - 4;  oy = gy * cell_pitch / 2 - 4;  big = 500;
    z0 = pad_height + floor_t;   // top of the floor slab = the cavity floor
    difference() {
        container(gx, gy, h, wall_t, floor_t);
        if (open_nx) translate([-big - ox, -big, z0]) cube([big, 2 * big, h]);
        if (open_px) translate([ox, -big, z0])        cube([big, 2 * big, h]);
        if (open_ny) translate([-big, -big - oy, z0]) cube([2 * big, big, h]);
        if (open_py) translate([-big, oy, z0])        cube([2 * big, big, h]);
    }
}
