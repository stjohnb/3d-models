include <_climbing_frame.scad>

// Print once, flat, with no supports. Keep frame_depth, post_size, beam_depth,
// bearer_z, net_width and net_mesh matching the frame and assembly so the net
// fits between the bearer and the far side rail.
scale(s) net_print();
