// =====================================
// Adjustable Bracket
// Two interlocking pieces with bolt adjustment
// =====================================
// One end has a rounded head to rest against a wall.
// The other end has a U-channel bracket that hooks over
// something below it (21mm gap along bar, 30mm deep down).
// The two pieces bolt together through a slot, making
// the total span adjustable (centre: 140mm).
//
// Measurements (from sketch):
//   Total span (adjustable): ~125-155mm (centre 140mm)
//   Bracket gap: 21mm (along bar axis)
//   Bracket depth: 30mm (downward)
//   Thickness: 10mm (1cm)
//   Bolt: M5 with nut and washers

$fn = 64;

// === Parameters (mm) ===
thickness       = 10;       // 1cm depth
bar_width       = 15;       // width of the overlap bar
bracket_gap     = 21;       // internal gap of bracket channel (along bar axis)
bracket_depth   = 30;       // bracket depth downward from bar
wall_t          = 5;        // bracket wall thickness
head_diameter   = 30;       // rounded wall-rest head diameter

// Bolt / slot
slot_length     = 30;       // adjustment slot length (~±15mm range)
bolt_clearance  = 5.5;      // M5 bolt clearance hole
washer_dia      = 12;       // washer recess diameter
washer_depth    = 2;        // washer recess depth

// Layout
total_span      = 140;      // centre of adjustment range
overlap         = 40;       // bar overlap at centre position

// Derived
piece_length    = (total_span + overlap) / 2;  // 90mm each

// === Piece A: Wall piece with rounded head ===
module piece_a() {
    difference() {
        union() {
            // Main bar
            cube([piece_length, bar_width, thickness]);

            // Rounded head at x=0 (wider than bar, for wall contact)
            translate([0, bar_width/2, 0])
                cylinder(d = head_diameter, h = thickness);
        }

        // Adjustment slot (in the overlap zone)
        slot_x = piece_length - overlap + 5;
        translate([slot_x, bar_width/2, -0.1])
            hull() {
                cylinder(d = bolt_clearance, h = thickness + 0.2);
                translate([slot_length, 0, 0])
                    cylinder(d = bolt_clearance, h = thickness + 0.2);
            }

        // Washer recess on bottom (nut side when assembled)
        translate([slot_x, bar_width/2, -0.1])
            hull() {
                cylinder(d = washer_dia, h = washer_depth + 0.1);
                translate([slot_length, 0, 0])
                    cylinder(d = washer_dia, h = washer_depth + 0.1);
            }
    }
}

// === Piece B: Bracket piece ===
// Bracket is a U-channel at the bar end, opening downward.
// Two walls drop down from the bar with a 21mm gap between them,
// connected at the bottom. Hooks over a rail/shelf edge from above.
module piece_b() {
    bracket_start_x = piece_length - 2*wall_t - bracket_gap;

    difference() {
        union() {
            // Main bar
            cube([piece_length, bar_width, thickness]);

            // Outer wall (at bar end)
            translate([piece_length - wall_t, -bracket_depth, 0])
                cube([wall_t, bracket_depth, thickness]);

            // Inner wall (bracket_gap away from outer wall)
            translate([bracket_start_x, -bracket_depth, 0])
                cube([wall_t, bracket_depth, thickness]);


        }

        // Bolt hole (round - the slot is on piece A)
        translate([overlap/2, bar_width/2, -0.1])
            cylinder(d = bolt_clearance, h = thickness + 0.2);

        // Washer recess on top (bolt head side when assembled)
        translate([overlap/2, bar_width/2, thickness - washer_depth])
            cylinder(d = washer_dia, h = washer_depth + 0.1);
    }
}

// === Assembly view ===
// This file is a shared library. Render individual pieces via:
//   piece_a.scad  ->  piece_a.stl
//   piece_b.scad  ->  piece_b.stl
