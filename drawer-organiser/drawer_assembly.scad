// Drawer Organiser — full assembly preview
// Render this file to generate drawer_assembly.stl.
//
// A viewing aid, not a printable part: it shows the whole 15 x 10 baseplate
// floor, rendered as one continuous slab, with a full set of containers seated
// on top, so the finished drawer reads at a glance. Each container is now also
// individually downloadable and bed-splittable as its own renderable —
// drawer_container_left, drawer_container_back_4x6,
// drawer_container_back_4x6_right, drawer_container_front_8x4,
// drawer_container_front_3x4, drawer_container_front_1x3 and
// drawer_container_front_1x1 — this file just arranges container() tubs over
// baseplate() to preview the layout described in layout.md ("Container
// layout").
//
// Container layout (looking down, -Y = drawer front, +Y = drawer back), from
// the maintainer's sketch in issue #324:
//   * a 3-wide container down the whole left side, full drawer depth;
//   * a back row (rows 5..10) of three 4 x 6 containers across the remaining
//     12 columns;
//   * a front row (rows 1..4) of an 8 x 4, a 3 x 4, and then a 1 x 3 with a
//     1 x 1 behind it in the last column.
// The four containers standing against a side wall (the left one, the
// back-right one, and the front 1 x 3 and 1 x 1) flare their outer wall outward
// with height to follow the drawer, which widens from 630mm at the floor to
// 670mm at the top (measured 669-670 — issue #326).
//
// The 3 x 4 implements the sketch's middle front container, which issue #324's
// text calls "3x3": the sketch draws it the full 4 rows deep, level with the
// 8 x 4 beside it, and 3 x 4 is what tiles the grid exactly. See layout.md.
//
// No rotate() here: the project sets viewer_rotate_x in meta.json, so the
// interactive viewer already tips the Z-up geometry upright. Adding a source
// rotate would double it up (the other drawer_* files are Z-up for the same
// reason).

include <_drawer_organiser.scad>

// --- Drawer + container parameters ---
// Drawer dimensions, the grid, and the side-wall flare all come from
// _drawer_organiser.scad, so this preview and the individual drawer_container_*
// files describe the same containers.

grid_x  = drawer_grid_x;   // baseplate cells across
grid_y  = drawer_grid_y;   // baseplate cells deep

height  = drawer_height; // container height (mm) — the full 69mm drawer height (issue #326)
wall_t  = 1.6;           // container wall thickness (mm)
floor_t = 1.6;           // container floor thickness above the pads (mm)

// Outward flare of a side-wall container: ~18.75mm of lean over the
// 4.75 -> 69mm shell, or 16.3 degrees from vertical (inside the usual
// 45-degree overhang rule). The preview is then ~630mm across at the floor and
// ~667mm at the rim, as the drawer is. See side_flare() for the derivation.
flare = side_flare(height);

// --- Cell-centre helpers (grid centred on the origin) ---
function cx(i) = (i - (grid_x - 1) / 2) * cell_pitch;   // x of column i (0-based)
function cy(j) = (j - (grid_y - 1) / 2) * cell_pitch;   // y of row j    (0-based)
function span_c(a, b) = (cx(a) + cx(b)) / 2;            // centre x of columns a..b
function span_r(a, b) = (cy(a) + cy(b)) / 2;            // centre y of rows a..b

// Colours are for the gallery thumbnail and the complex-interior orthographic
// views, which CI renders straight from this .scad. STL export is monochrome, so
// the interactive viewer shows this file as a single user-recolourable model:
// the eight containers read as one shape there, which is accepted here — they are
// separated by geometry (walls and gaps), and the coloured thumbnail plus the
// table in layout.md carry the layout. The alternative is meta.json's `assembly`
// composite (docs/web-viewer.md), which keeps colours in the viewer but needs
// each container emitted as its own co-registered STL matching its assembly
// position. The containers now exist as renderables, but each is centred on the
// origin for printing rather than co-registered at its assembly position, so
// the composite path is still not free and is still not taken here.
//
// Hex values are taken directly from filament-colors.json, the project's colour
// source of truth.

// --- Floor: one continuous baseplate slab ---
color("#9e9e9e") baseplate(grid_x, grid_y);   // Grey (filament palette "Grey")

// --- Containers seated on the floor (pads drop into the sockets) ---

// Left: 3 wide, full depth; flares out to the left (-X).
color("#64b5f6")                            // Blue (filament palette "Blue")
    translate([span_c(0, 2), span_r(0, 9), 0])
        container(3, 10, height, wall_t, floor_t, fnx = flare);

// Back row: columns 4..15 x rows 5..10, three 4 x 6 containers side by side.
// Only the last one reaches the drawer wall, so only it flares (+X).
color("#43a047")                            // Green (filament palette "Green")
    translate([span_c(3, 6), span_r(4, 9), 0])
        container(4, 6, height, wall_t, floor_t);
color("#e53935")                            // Red (filament palette "Red")
    translate([span_c(7, 10), span_r(4, 9), 0])
        container(4, 6, height, wall_t, floor_t);
color("#fdd835")                            // Yellow (filament palette "Yellow")
    translate([span_c(11, 14), span_r(4, 9), 0])
        container(4, 6, height, wall_t, floor_t, fpx = flare);

// Front row: columns 4..15 x rows 1..4. An 8-wide tub, then a 3-wide one, then
// the last column carries a 1 x 3 with a 1 x 1 behind it — both against the
// drawer wall, so both flare out to the right (+X).
color("#fb8c00")                            // Orange (filament palette "Orange")
    translate([span_c(3, 10), span_r(0, 3), 0])
        container(8, 4, height, wall_t, floor_t);
color("#f5f5f5")                            // White (filament palette "White")
    translate([span_c(11, 13), span_r(0, 3), 0])
        container(3, 4, height, wall_t, floor_t);
color("#2a2a2a")                            // Black (filament palette "Black")
    translate([cx(14), span_r(0, 2), 0])
        container(1, 3, height, wall_t, floor_t, fpx = flare);
// Eight containers, seven non-grey filament colours: Green comes round again
// here, on the one tub that touches no other green.
color("#43a047")                            // Green (filament palette "Green")
    translate([cx(14), cy(3), 0])
        container(1, 1, height, wall_t, floor_t, fpx = flare);
