// Drawer Organiser — full assembly preview
// Render this file to generate drawer_assembly.stl.
//
// A viewing aid, not a printable part: it shows the whole 15 x 10 baseplate
// floor, rendered as one continuous slab, with a full set of containers seated
// on top, so the finished drawer reads at a glance. Each container is now also
// individually downloadable and bed-splittable as its own renderable —
// drawer_container_left, drawer_container_back, drawer_container_front_4x7,
// and drawer_container_front_right — this file just arranges container() tubs
// over baseplate() to preview the layout described in layout.md ("Container
// layout").
//
// Container layout (looking down, -Y = drawer front, +Y = drawer back):
//   * a 3-wide container down the whole left side, full drawer depth;
//   * a 12-wide container across the rest of the back, 3 rows deep;
//   * the remaining front block split into three equal 4-wide areas.
// The three containers standing against a side wall (the left one, the back-row
// one, and the front-right one) flare their outer wall outward with height to
// follow the drawer, which widens from 630mm at the floor to 665mm at the top.
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

z_units = 8;             // container height units -> 56mm tall
wall_t  = 1.6;           // container wall thickness (mm)
floor_t = 1.6;           // container floor thickness above the pads (mm)

// Outward flare of a side-wall container: ~12.95mm of lean over the
// 4.75 -> 56mm shell, or 14.2 degrees from vertical (inside the usual
// 45-degree overhang rule). The preview is then ~630mm across at the floor and
// ~655mm at the rim, as the drawer is. See side_flare() for the derivation.
flare = side_flare(z_units);

// --- Cell-centre helpers (grid centred on the origin) ---
function cx(i) = (i - (grid_x - 1) / 2) * cell_pitch;   // x of column i (0-based)
function cy(j) = (j - (grid_y - 1) / 2) * cell_pitch;   // y of row j    (0-based)
function span_c(a, b) = (cx(a) + cx(b)) / 2;            // centre x of columns a..b
function span_r(a, b) = (cy(a) + cy(b)) / 2;            // centre y of rows a..b

// Colours are for the gallery thumbnail and the complex-interior orthographic
// views, which CI renders straight from this .scad. STL export is monochrome, so
// the interactive viewer shows this file as a single user-recolourable model:
// the five containers read as one shape there, which is accepted here — they are
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
        container(3, 10, z_units, wall_t, floor_t, fnx = flare);

// Back: across the remaining width (columns 4..15), 3 rows deep; flares out to
// the right (+X), where its end stands against the drawer wall.
color("#43a047")                            // Green (filament palette "Green")
    translate([span_c(3, 14), span_r(7, 9), 0])
        container(12, 3, z_units, wall_t, floor_t, fpx = flare);

// Front block, columns 4..15 x rows 1..7, split into three (4 + 4 + 4 wide).
color("#fb8c00")                            // Orange (filament palette "Orange")
    translate([span_c(3, 6), span_r(0, 6), 0])
        container(4, 7, z_units, wall_t, floor_t);
color("#e53935")                            // Red (filament palette "Red")
    translate([span_c(7, 10), span_r(0, 6), 0])
        container(4, 7, z_units, wall_t, floor_t);
// Front-right stands against the drawer wall, so it flares out to the right.
color("#fdd835")                            // Yellow (filament palette "Yellow")
    translate([span_c(11, 14), span_r(0, 6), 0])
        container(4, 7, z_units, wall_t, floor_t, fpx = flare);
