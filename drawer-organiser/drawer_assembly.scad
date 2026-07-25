// Drawer Organiser — full assembly preview
// Render this file to generate drawer_assembly.stl.
//
// A viewing aid, not a printable part: it shows the whole 14 x 10 baseplate
// floor (rendered as one continuous slab, plus the four side-filler strips)
// with a full set of containers seated on top, so the finished drawer reads at
// a glance. The individual printable parts are the other drawer_* files; this
// file just arranges container() tubs over baseplate()/filler() to preview the
// layout described in layout.md ("Container layout").
//
// Container layout (looking down, -Y = drawer front, +Y = drawer back):
//   * a 3-wide container down the whole left side, full drawer depth;
//   * a container across the rest of the back, 3 rows deep;
//   * the remaining front block split into three roughly equal areas
//     (4, 4 and 3 cells wide).
// The three containers standing against a side wall (the left one, the back-row
// one, and the front-right one) flare their outer wall outward with height to
// follow the drawer, which widens from 628mm at the floor to 665mm at the top.
//
// No rotate() here: the project sets viewer_rotate_x in meta.json, so the
// interactive viewer already tips the Z-up geometry upright. Adding a source
// rotate would double it up (the other drawer_* files are Z-up for the same
// reason).

include <_drawer_organiser.scad>

// --- Drawer + container parameters ---
drawer_bottom_w = 628;   // drawer width at the floor (mm)
drawer_top_w    = 665;   // drawer width at the top (mm)
drawer_height   = 69;    // drawer depth, floor to top (mm)

grid_x  = 14;            // baseplate cells across
grid_y  = 10;            // baseplate cells deep
fill_w  = 19.5;          // side filler strip width (mm), matches drawer_filler

z_units = 8;             // container height units -> 56mm tall
wall_t  = 1.6;           // container wall thickness (mm)
floor_t = 1.6;           // container floor thickness above the pads (mm)

// Outward flare at the top of a side-wall container: the drawer gains
// (665 - 628)/2 = 18.5mm of width per side over its 69mm height, so a container
// H mm tall can lean its outer wall out by that fraction of 18.5mm and still
// clear the sloping drawer wall.
container_h = z_units * height_unit;
flare = (drawer_top_w - drawer_bottom_w) / 2 / drawer_height * container_h;

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
// each container emitted as its own co-registered STL — five more non-printable
// renderables and gallery cards for a preview aid. Not worth it here.
//
// Hex values are taken directly from filament-colors.json, the project's colour
// source of truth.

// --- Floor: one continuous baseplate slab + four filler strips ---
color("#9e9e9e") {                          // Grey (filament palette "Grey")
    baseplate(grid_x, grid_y);
    half_w = grid_x * cell_pitch / 2;       // 294mm to the baseplate edge
    for (sx = [-1, 1], j = [0, 1])
        translate([sx * (half_w + fill_w / 2), (j - 0.5) * 5 * cell_pitch, 0])
            filler(5, fill_w);
}

// --- Containers seated on the floor (pads drop into the sockets) ---

// Left: 3 wide, full depth; flares out to the left (-X).
color("#64b5f6")                            // Blue (filament palette "Blue")
    translate([span_c(0, 2), span_r(0, 9), 0])
        container(3, 10, z_units, wall_t, floor_t, fnx = flare);

// Back: across the remaining width (columns 4..14), 3 rows deep; flares out to
// the right (+X), where its end stands against the drawer wall.
color("#43a047")                            // Green (filament palette "Green")
    translate([span_c(3, 13), span_r(7, 9), 0])
        container(11, 3, z_units, wall_t, floor_t, fpx = flare);

// Front block, columns 4..14 x rows 1..7, split into three (4 + 4 + 3 wide).
color("#fb8c00")                            // Orange (filament palette "Orange")
    translate([span_c(3, 6), span_r(0, 6), 0])
        container(4, 7, z_units, wall_t, floor_t);
color("#e53935")                            // Red (filament palette "Red")
    translate([span_c(7, 10), span_r(0, 6), 0])
        container(4, 7, z_units, wall_t, floor_t);
// Front-right stands against the drawer wall, so it flares out to the right.
color("#fdd835")                            // Yellow (filament palette "Yellow")
    translate([span_c(11, 13), span_r(0, 6), 0])
        container(3, 7, z_units, wall_t, floor_t, fpx = flare);
