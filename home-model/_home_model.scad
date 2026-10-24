// =====================================
// Home massing model
// 1:100 printable massing model of a two-storey semi with rear and side
// extensions, its plot and the garden room, from the architect's 1:50
// drawings. All figures below are real millimetres.
// =====================================
// Parts:
//   home_house        -> home_house.stl        house, roofs, bay, canopy, chimney
//   home_garden_room  -> home_garden_room.stl  L-shaped shower/office/workshop
//   home_site_front   -> home_site_front.stl   front plot tile (Y up to 15000)
//   home_site_rear    -> home_site_rear.stl    rear plot tile (Y from 15000)
//   home_assembly     -> home_assembly.stl     viewing aid, not a printable part
//
// Site frame: X east (party wall side), Y towards the rear garden, Z up;
// X = 0 at the west face of the rear extension, Y = 0 at the main house
// front face. scale_denominator divides everything at the end.

$fn = 64;

scale_denominator = 100;
s = 1 / scale_denominator;

// Print-size features (printed mm x scale_denominator)
base_t    = 3   * scale_denominator;
recess_d  = 0.6 * scale_denominator;
relief_h  = 0.5 * scale_denominator;
opening_d = 0.5 * scale_denominator;
fence_t   = 1.2 * scale_denominator;
fit_clear = 0.2 * scale_denominator;
eps = 1;

// Plot
plot_x0 = -1050;  plot_x1 =  7670;  plot_y0 = -6300;  plot_y1 = 31200;
tile_split_y = 15000;
patio_y0 = 12980;  patio_y1 = 14750;  drive_x0 = 5600;
fence_h  = 1800;  fence_y0 = 4400;  east_fence_y0 = 12980;

// Main house
main_x0 = 1970;  main_x1 = 7670;  main_y0 = 0;  main_y1 = 5871;
main_eaves_h = 5300;  main_ridge_h = 6700;  main_ridge_y = (main_y0 + main_y1) / 2;
front_overhang = 300;  verge_overhang = 150;
bay_x0 = 2820;  bay_x1 = 5370;  bay_proj = 900;  bay_h = 2700;
canopy_y = -1000;  canopy_z0 = 2350;  canopy_z1 = 2800;  canopy_t = 150;

// Rear extension and first-floor rear block
rear_x0 = 0;  rear_x1 = 7670;  rear_y0 = main_y1;  rear_y1 = 12980;
ff_x0 = 2150;  ff_x1 = 7670;  rear_eaves_h = 5100;  rear_ridge_h = 6400;
rear_ridge_x = (ff_x0 + ff_x1) / 2;  hip_len = (ff_x1 - ff_x0) / 2;
side_x0 = 0;  side_x1 = main_x0;  side_y0 = 4370;  side_y1 = main_y1;
flat_h = 3100;
chim_x0 = 1870;  chim_x1 = 2370;  chim_y0 = 3250;  chim_y1 = 3750;  chim_h = 7500;
pot_d = 250;  pot_h = 300;
rooflight_x0 = 800;  rooflight_x1 = 1550;  rooflight_y = [7900, 9700];  rooflight_l = 1000;  rooflight_d = 50;

// Garden room
gr_x0 = -280;  gr_x1 = 7320;  gr_y1 = 30855;  gr_north_y0 = gr_y1 - 3400;
gr_west_x1 = 3020;  gr_west_y0 = gr_north_y0 - 3200;
gr_wall_h = 2530;  gr_roof_t = 250;  gr_h = gr_wall_h + gr_roof_t;
cov_x1 = 3420;  cov_y0 = gr_west_y0 - 5000;
post_w = 150;  low_wall_t = 215;  low_wall_h = 750;

module box(x0, x1, y0, y1, z0, z1) { translate([x0, y0, z0]) cube([x1 - x0, y1 - y0, z1 - z0]); }
module cut_south(y, x0, x1, z0, z1) { box(x0, x1, y - eps, y + opening_d, z0 - eps, z1); }
module cut_north(y, x0, x1, z0, z1) { box(x0, x1, y - opening_d, y + eps, z0 - eps, z1); }
module cut_west(x, y0, y1, z0, z1)  { box(x - eps, x + opening_d, y0, y1, z0 - eps, z1); }
module cut_east(x, y0, y1, z0, z1)  { box(x - opening_d, x + eps, y0, y1, z0 - eps, z1); }
module yz_prism(x0, x1, pts) { translate([x0, 0, 0]) rotate([90, 0, 90]) linear_extrude(x1 - x0) polygon(pts); }

module main_roof() {
    k = (main_ridge_h - main_eaves_h) / (main_ridge_y - main_y0);
    yz_prism(main_x0 - verge_overhang, main_x1, [
        [main_y0 - front_overhang, main_eaves_h - front_overhang * k],
        [main_ridge_y, main_ridge_h], [main_y1, main_eaves_h]]);
}
// Hip prism starts under the main ridge so the union forms the valleys.
module rear_roof() {
    hull() {
        box(ff_x0, ff_x1, main_ridge_y, rear_y1, rear_eaves_h - eps, rear_eaves_h);
        box(rear_ridge_x - 1, rear_ridge_x + 1, main_ridge_y, rear_y1 - hip_len, rear_ridge_h - 1, rear_ridge_h);
    }
}
module canopy() {
    yz_prism(bay_x0, main_x1, [[canopy_y, canopy_z0], [eps, canopy_z1],
        [eps, canopy_z1 - canopy_t], [canopy_y, canopy_z0 - canopy_t]]);
}
module chimney() {
    box(chim_x0, chim_x1, chim_y0, chim_y1, 0, chim_h);
    for (x = [chim_x0 + 125, chim_x1 - 125])
        translate([x, (chim_y0 + chim_y1) / 2, chim_h - eps]) cylinder(d = pot_d, h = pot_h + eps);
}
module house_real() {
    difference() {
        union() {
            box(main_x0, main_x1, main_y0, main_y1, 0, main_eaves_h);
            box(rear_x0, rear_x1, rear_y0 - eps, rear_y1, 0, flat_h);
            box(ff_x0, ff_x1, rear_y0 - eps, rear_y1, 0, rear_eaves_h);
            box(side_x0, side_x1 + eps, side_y0, side_y1 + eps, 0, flat_h);
            box(bay_x0, bay_x1, -bay_proj, eps, 0, bay_h);
            main_roof(); rear_roof(); canopy(); chimney();
        }
        cut_south(-bay_proj, 3020, 5170, 800, 2280);      // bay window
        cut_south(main_y0, 5960, 7310, 0, 2180);          // front door + side light
        cut_south(main_y0, 2861, 4570, 3261, 4731);       // FF window west
        cut_south(main_y0, 5971, 6560, 3331, 4731);       // FF window over door
        cut_south(side_y0, 1000, 1900, 0, 2280);          // side extension door
        cut_west(rear_x0, 5900, 6800, 0, 2080);           // kitchen strip door
        cut_west(main_x0, 4800, 5700, flat_h + 50, 4810); // FF escape window
        cut_west(ff_x0, 6865, 7764, 3932, 4682);          // bath
        cut_west(ff_x0, 8456, 9055, 3932, 4682);          // en-suite
        cut_north(rear_y1, 1302, 6811, 180, 2280);        // sliding doors
        cut_north(rear_y1, 5151, 6871, 3512, 4862);       // principal bed window
        cut_north(rear_y1, 3202, 3782, 3512, 4862);       // dressing window
        for (y = rooflight_y) box(rooflight_x0, rooflight_x1, y, y + rooflight_l, flat_h - rooflight_d, flat_h + eps);
    }
}
module garden_room_real() {
    difference() {
        union() {
            box(gr_x0, gr_x1, gr_north_y0, gr_y1, 0, gr_h);
            box(gr_x0, gr_west_x1, gr_west_y0, gr_north_y0 + eps, 0, gr_h);
            box(gr_x0, cov_x1, cov_y0, gr_west_y0 + eps, gr_wall_h, gr_h);
            for (x = [gr_x0, cov_x1 - post_w], y = [cov_y0, (cov_y0 + gr_west_y0) / 2])
                box(x, x + post_w, y, y + post_w, 0, gr_wall_h + eps);
            box(gr_x0, gr_x0 + low_wall_t, cov_y0, gr_west_y0 + eps, 0, low_wall_h);
        }
        cut_south(gr_west_y0, 1020, 2620, 0, 2100);   // office doors to covered area
        cut_south(gr_north_y0, 4600, 6730, 0, 2100);  // workshop double door
        cut_east(gr_west_x1, 24355, 25155, 0, 2100);  // office door
        cut_east(gr_west_x1, 25255, 26555, 950, 2200);// office window
        cut_west(gr_x0, 29455, 30055, 1500, 2200);    // shower window
    }
}
module house_footprint_2d() {
    translate([main_x0, main_y0]) square([main_x1 - main_x0, main_y1 - main_y0]);
    translate([bay_x0, -bay_proj]) square([bay_x1 - bay_x0, bay_proj + eps]);
    translate([rear_x0, rear_y0 - eps]) square([rear_x1 - rear_x0, rear_y1 - rear_y0 + eps]);
    translate([side_x0, side_y0]) square([side_x1 - side_x0 + eps, side_y1 - side_y0 + eps]);
}
module garden_room_footprint_2d() {
    translate([gr_x0, gr_north_y0]) square([gr_x1 - gr_x0, gr_y1 - gr_north_y0]);
    translate([gr_x0, gr_west_y0]) square([gr_west_x1 - gr_x0, gr_north_y0 - gr_west_y0 + eps]);
    translate([gr_x0, cov_y0]) square([cov_x1 - gr_x0, gr_west_y0 - cov_y0 + eps]);
}
module fences() {
    box(plot_x0, plot_x0 + fence_t, fence_y0, plot_y1, 0, fence_h);
    box(plot_x1 - fence_t, plot_x1, east_fence_y0, plot_y1, 0, fence_h);
    box(plot_x0, plot_x1, plot_y1 - fence_t, plot_y1, 0, fence_h);
    box(plot_x0, 0, fence_y0, fence_y0 + fence_t, 0, fence_h);
}
module relief() {
    box(plot_x0, plot_x1, patio_y0, patio_y1, 0, base_t + relief_h);
    box(plot_x0, 0, plot_y0, rear_y1, 0, base_t + relief_h);
    box(drive_x0, plot_x1, plot_y0, -bay_proj, 0, base_t + relief_h);
}
module tile_real(y0, y1) {
    difference() {
        union() {
            box(plot_x0, plot_x1, y0, y1, 0, base_t);
            intersection() { box(plot_x0, plot_x1, y0, y1, 0, base_t + relief_h + eps); relief(); }
            intersection() { box(plot_x0, plot_x1, y0, y1, 0, base_t + fence_h + eps); translate([0, 0, base_t - eps]) fences(); }
        }
        translate([0, 0, base_t - recess_d]) linear_extrude(recess_d + relief_h + 2 * eps)
            offset(delta = fit_clear) { house_footprint_2d(); garden_room_footprint_2d(); }
    }
}
module site_front_real() { tile_real(plot_y0, tile_split_y); }
module site_rear_real()  { tile_real(tile_split_y, plot_y1); }
module home_assembly_real() {
    site_front_real(); site_rear_real();
    translate([0, 0, base_t - recess_d]) { house_real(); garden_room_real(); }
}
