include <_climbing_frame.scad>

// Trapezoid net for the A-frame end. Print once, flat, with no supports. Keep
// frame_depth, post_size, beam_depth, bearer_z and net_mesh matching the A-frame
// frame and assembly so the net fits between the bearer, the legs and the apex tie.
aframe_end = true;
scale(s) net_print();
