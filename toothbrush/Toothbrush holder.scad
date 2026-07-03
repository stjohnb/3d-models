// =====================================
// Electric Toothbrush Holder - Full Assembly
// Renders the complete holder oriented for the Three.js web viewer
// =====================================

include <_toothbrush_holder.scad>

// ---- Render ----
// Outer rotate converts Z-up (OpenSCAD) to Y-up (Three.js viewer)
rotate([-90, 0, 0])
    toothbrush_holder();
