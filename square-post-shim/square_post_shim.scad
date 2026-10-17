// =====================================
// Square Post Shim (L-shaped corner shim)
// Takes up play between a ~30 mm square exercise-bike post and its socket.
// Wraps one corner of the post, shimming two adjacent faces at once; the
// flange hooks over the socket collar rim so it can't drop down the tube.
// Modeled flange-down in print orientation: prints upright, no supports.
// =====================================

$fn = 64;

// ---- Parameters (mm) ----
post_w = 30.2;      // post outer width (caliper, smaller axis)
post_r = 2;         // post outer corner radius
shim_t = 0.6;       // wall thickness on each face
leg_len = 20;       // length of each leg along a post face, from the outer corner
shim_len = 40;      // insertion depth below the flange
lip_depth = 4;      // flange reach outward over the socket rim
lip_t = 2;          // flange thickness
lead_in = 5;        // height of the tapered tip on the free end
lead_in_t = 0.2;    // wall thickness at the very tip

// ---- Derived ----
half = post_w / 2;
total_h = lip_t + shim_len;

assert(shim_t > 0, "shim_t must be positive");
assert(lip_depth > 0, "lip_depth must be positive");
assert(lead_in < shim_len, "lead_in must be shorter than shim_len");
assert(lead_in_t <= shim_t, "lead_in_t must not exceed shim_t");
assert(leg_len > post_r && leg_len < post_w, "leg_len must be between post_r and post_w");

// Rounded square centred on the origin with half-width h and corner radius r
module rounded_square(h, r) {
    offset(r = r) square(2 * (h - r), center = true);
}

module square_post_shim() {
    intersection() {
        difference() {
            union() {
                // Flange over the socket rim
                linear_extrude(height = lip_t)
                    rounded_square(half + shim_t + lip_depth, post_r + shim_t + lip_depth);
                // Shim wall with tapered lead-in at the free end
                hull() {
                    linear_extrude(height = 0.01)
                        rounded_square(half + shim_t, post_r + shim_t);
                    translate([0, 0, total_h - lead_in])
                        linear_extrude(height = 0.01)
                            rounded_square(half + shim_t, post_r + shim_t);
                    translate([0, 0, total_h - 0.01])
                        linear_extrude(height = 0.01)
                            rounded_square(half + lead_in_t, post_r + lead_in_t);
                }
            }
            // The post itself
            translate([0, 0, -1])
                linear_extrude(height = total_h + 2)
                    rounded_square(half, post_r);
        }
        // Keep only one corner: two legs of leg_len along adjacent faces
        translate([half - leg_len, half - leg_len, -1])
            cube([leg_len + shim_t + lip_depth + 1, leg_len + shim_t + lip_depth + 1, total_h + 2]);
    }
}

square_post_shim();
