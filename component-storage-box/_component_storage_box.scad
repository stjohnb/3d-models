// Component storage box library - 250 x 250 mm open-top organiser for the
// Bambu Lab A1 plate: a 5 x 5 grid of 50 mm cells tiled into compartments.
// No top-level geometry; render component_box.scad.

$fn = 64;

plate_xy   = 250;  // outer footprint, square (mm)
outer_h    = 70;   // overall height (mm)
cells      = 5;    // grid cells per side
wall_outer = 2.0;  // perimeter wall (mm)
wall_inner = 1.2;  // divider wall (mm)
floor_t    = 2.0;  // floor thickness (mm)
corner_r   = 4;    // outer corner radius (mm)
cavity_r   = 2;    // cavity corner radius (mm)

// [col, row, cols_wide, rows_deep] in whole cells; columns from the left
// (-X), rows from the front (-Y).
compartments = [
    [0, 4, 3, 1],   // A: 3x1 across the back-left
    [3, 4, 2, 1],   // B: 2x1 across the back-right
    [0, 3, 3, 1],   // C: 3x1 left-middle, upper
    [0, 2, 3, 1],   // D: 3x1 left-middle, lower
    [3, 2, 1, 2],   // E: 1x2 column beside C and D
    [4, 3, 1, 1],   // s: single cell, right edge
    [4, 2, 1, 1],   // t: single cell, right edge
    [0, 0, 1, 2],   // p: 1x2 column, front-left
    [1, 0, 1, 2],   // q: 1x2 column beside p
    [2, 0, 3, 2],   // H: 3x2 front-right
];

pitch    = plate_xy / cells;
cavity_h = outer_h - floor_t;

coverage = [for (i = [0 : cells - 1], j = [0 : cells - 1])
    len([for (c = compartments)
        if (i >= c[0] && i < c[0] + c[2] && j >= c[1] && j < c[1] + c[3]) 1])];
assert(min(coverage) == 1 && max(coverage) == 1,
       "compartments must tile the grid with every cell in exactly one compartment");
assert(max([for (c = compartments) max(c[2], c[3])]) <= 3,
       "no compartment may span 4 or more cells");
assert(wall_inner < pitch - 2 * cavity_r && wall_outer < pitch - cavity_r,
       "walls too thick for the cell pitch");

// Rounded-rectangle prism from (x0,y0) to (x1,y1), base at z=0.
module rrect(x0, y0, x1, y1, h, r) {
    hull()
        for (x = [x0 + r, x1 - r], y = [y0 + r, y1 - r])
            translate([x, y, 0]) cylinder(h = h, r = r);
}

// Interior block of one compartment: inset by the outer wall on perimeter
// edges and half a divider wall on interior edges.
module cavity(c) {
    x0 = c[0] * pitch + (c[0] == 0 ? wall_outer : wall_inner / 2);
    y0 = c[1] * pitch + (c[1] == 0 ? wall_outer : wall_inner / 2);
    x1 = (c[0] + c[2]) * pitch - (c[0] + c[2] == cells ? wall_outer : wall_inner / 2);
    y1 = (c[1] + c[3]) * pitch - (c[1] + c[3] == cells ? wall_outer : wall_inner / 2);
    translate([0, 0, floor_t])
        rrect(x0, y0, x1, y1, cavity_h + 1, cavity_r);
}

module component_box() {
    translate([-plate_xy / 2, -plate_xy / 2, 0])
        difference() {
            rrect(0, 0, plate_xy, plate_xy, outer_h, corner_r);
            for (c = compartments) cavity(c);
        }
}
