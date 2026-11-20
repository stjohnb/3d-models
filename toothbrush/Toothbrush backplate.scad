// =====================================
// Toothbrush Holder Backplate - Print File
// Base + stand + plates with dovetail rails
// Print lying on its back (flat on bed)
// =====================================

include <_toothbrush_holder.scad>

// Print orientation, NOT a viewer hack: toothbrush_backplate() stands upright
// in the library; this lays it on its back, flat on the bed. Keep it.
rotate([-90, 0, 0])
    toothbrush_backplate();
