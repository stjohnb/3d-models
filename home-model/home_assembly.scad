include <_home_model.scad>

// Viewing aid, not a printable part.
$fn = 32;
scale(s) translate([-plot_x0, -plot_y0, 0]) home_assembly_real();
