// =====================================
// Bench Dog Blank
// Flush plug for countersunk 18mm bench dog holes in 18mm ply
// Removal: needle-nose pliers grip the bar between the two top notches
// Modeled top-face-down: prints flat on the bed, no supports
// =====================================

$fn = 64;

// ---- Parameters (mm) ----
hole_d = 18;        // bench dog hole diameter (caliper)
top_d = 26.5;       // countersink opening diameter at the surface (caliper)
taper_depth = 2.5;  // depth of the 45-degree head taper below the surface
ply_thickness = 18; // bench top plywood thickness = total blank height
clearance = 0.3;    // diametral fit clearance applied to all outer diameters
lead_in = 0.5;      // 45-degree insertion chamfer on the shaft's free end
top_trim = 0.5;     // shaved off the top face so blanks sit flush instead of proud

// ---- Pliers grip recess (fixed grip detail, not customized) ----
notch_w = 3.5;      // width of each notch, across the grip bar
notch_len = 7;      // length of each notch, along the grip bar
notch_depth = 3.5;  // notch depth below the top face
bar_w = 3;          // grip bar left between the notches, flush with the top face

// ---- Derived (45-degree taper: base shrinks 2*taper_depth) ----
head_base_d = top_d - 2 * taper_depth;   // 21.5 at defaults
shaft_d = hole_d - clearance;            // 17.7 at defaults
// Head frustum height after trimming top_trim off its (bed-side) top face
head_h = taper_depth - top_trim;
// Frustum diameter at the trimmed top face (linear interpolation along the taper)
head_top_d = (top_d - clearance) + (head_base_d - top_d) * (top_trim / taper_depth);

assert(head_base_d - clearance >= shaft_d,
       "taper_depth too deep: head base is narrower than the shaft");
assert(head_h > 0, "top_trim must be less than taper_depth");

// farthest corner of a notch must stay inside the shaft wall
notch_reach = sqrt(pow(bar_w / 2 + notch_w, 2) + pow(notch_len / 2, 2));
assert(notch_reach <= shaft_d / 2 - 1.2,
       "hole_d too small for the pliers grip notches");

module bench_dog_blank() {
    difference() {
        union() {
            // Head frustum: bed face is the bench-top face, top_trim already
            // shaved off so it sits flush instead of proud, tapering inward
            // at 45 degrees
            cylinder(d1 = head_top_d, d2 = head_base_d - clearance,
                     h = head_h);
            // Shaft, stopping short of full height by the lead-in chamfer
            translate([0, 0, head_h])
                cylinder(d = shaft_d, h = ply_thickness - taper_depth - lead_in);
            // Insertion lead-in chamfer at the shaft's free end
            translate([0, 0, ply_thickness - top_trim - lead_in])
                cylinder(d1 = shaft_d, d2 = shaft_d - 2 * lead_in, h = lead_in);
        }
        // Two rectangular notches flanking the grip bar: needle-nose jaws
        // drop into the notches and close on the bar to pull the blank
        for (s = [-1, 1])
            translate([s * (bar_w + notch_w) / 2, 0, notch_depth / 2 - 0.01])
                cube([notch_w, notch_len, notch_depth + 0.02], center = true);
    }
}

bench_dog_blank();
