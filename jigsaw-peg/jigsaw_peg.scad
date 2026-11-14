// =====================================
// Jigsaw Peg
// Replacement peg for a missing peg in a jigsaw item
// Photo/caliper readings: hole 3.78mm inside jaws, 6mm deep (reporter);
// existing peg 5.81mm across the head, standing 7.16-7.66mm above the piece
// Modeled head-top-down: prints flat on the bed, no supports
// =====================================

$fn = 64;

// ---- Parameters (mm) ----
hole_d = 3.8;        // hole diameter (caliper, inside jaws)
hole_depth = 6;      // hole depth (reporter)
seat_gap = 0.5;      // shank stops this far short of the hole bottom so the head seats
head_d = 5.8;        // head diameter (caliper, across the existing peg)
head_h = 7.4;        // peg height standing proud of the piece (7.16-7.66 measured)
head_chamfer = 0.5;  // 45-degree edge break on the head's top
clearance = 0.2;     // diametral fit clearance; slip fit, glue in
lead_in = 0.4;       // 45-degree insertion chamfer on the shank's free end

// ---- Derived ----
shank_d = hole_d - clearance;        // 3.6 at defaults
shank_len = hole_depth - seat_gap;   // 5.5 at defaults, never longer than the hole
head_top_d = head_d - 2 * head_chamfer;

assert(seat_gap >= 0, "seat_gap must not be negative or the shank is longer than the hole");
assert(shank_len > lead_in, "shank_len must exceed lead_in");
assert(head_top_d > 0, "head_chamfer too large for head_d");
assert(head_chamfer < head_h, "head_chamfer must be less than head_h");
assert(shank_d > 2 * lead_in, "shank_d must exceed 2 * lead_in");
assert(head_d > shank_d, "head_d must be larger than shank_d");

module jigsaw_peg() {
    // Head top face on the bed (z = 0), shank rising from it
    cylinder(d1 = head_top_d, d2 = head_d, h = head_chamfer);
    translate([0, 0, head_chamfer])
        cylinder(d = head_d, h = head_h - head_chamfer);
    translate([0, 0, head_h])
        cylinder(d = shank_d, h = shank_len - lead_in);
    translate([0, 0, head_h + shank_len - lead_in])
        cylinder(d1 = shank_d, d2 = shank_d - 2 * lead_in, h = lead_in);
}

jigsaw_peg();
