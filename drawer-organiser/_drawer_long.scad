// Drawer Organiser — second drawer (long implements)
// Library: the long-implement drawer's dimensions on top of _drawer_organiser.scad.
// Issue clw_01M43Z7AXXMZQCK6ZDVCBB6K4D; see layout.md "Second drawer: long implements".
//   390mm floor width ("39 cm" — rough, so 2mm slack is kept), 425mm front to back.
//   LEFT wall flares like the first drawer (20mm over 69mm); RIGHT wall is vertical.
//   Height not remeasured — the first drawer's 69mm is assumed.
// The 9 x 10 grid sits flush to the LEFT wall at the floor, so the taper relative
// to the grid edge is exactly the first drawer's and drawer_container_left_front /
// _back fit unchanged. All width slack goes RIGHT: a 10mm filler strip swallows
// the right-hand tile tabs and leaves 2mm of fit slack.

include <_drawer_organiser.scad>

long_drawer_floor_w  = 390;   // floor width (issue: "39 cm")
long_drawer_depth    = 425;   // front to back
long_drawer_height   = drawer_height;                        // 69, assumed
long_drawer_taper    = (drawer_top_w - drawer_bottom_w) / 2; // 20, LEFT wall only
long_drawer_grid_x   = 9;     // floor(390 / 42)
long_drawer_grid_y   = 10;    // floor(425 / 42)
long_drawer_slack    = 2;     // fit slack against the vertical right wall
long_drawer_fill_w   = long_drawer_floor_w - long_drawer_grid_x * cell_pitch - long_drawer_slack;  // 10

// Outward top offset for a container against the LEFT wall: wall leans out
// long_drawer_taper over long_drawer_height, the outer face starts 0.25mm
// inboard of the grid edge, the rim stops container_wall_clear short. 18.75mm
// at h = 69 — the same as side_flare(69).
function long_left_flare(h) =
    long_drawer_taper * h / long_drawer_height
    - container_wall_clear + (4 - pad_r_top);

assert(abs(long_left_flare(drawer_height) - side_flare(drawer_height)) < 1e-9,
       "long_left_flare must match side_flare so the existing left container pieces fit");
