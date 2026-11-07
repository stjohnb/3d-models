// Workshop vacuum blast gate — assembly preview (closed position)
// Sources stay Z-up; the web viewer applies the Y-up conversion.
include <_blast_gate.scad>

{
    gate_body();
    // Blade fully closed: trailing edge flush with -X face of body; leading edge against end wall.
    translate([-body_d/2, 0, 0]) gate_blade();
}
