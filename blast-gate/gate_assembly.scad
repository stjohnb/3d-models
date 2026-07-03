// Workshop vacuum blast gate — assembly preview (closed position)
// Z-up → Y-up rotation per project viewer convention.
include <_blast_gate.scad>

rotate([-90, 0, 0]) {
    gate_body();
    // Blade fully closed: trailing edge flush with -X face of body; leading edge against end wall.
    translate([-body_d/2, 0, 0]) gate_blade();
}
