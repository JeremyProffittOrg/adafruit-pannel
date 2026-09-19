// First-class two-piece 1.00 in control case (YAPP-style shell).
// Closed tray: floor + left + right + front + back walls.
// Lid is a shoebox cover: plate + outer skirt that drops over the tray.
// Short world-Z pegs (C_PEG_H) sit in blind sockets in the wall tops.
// M3 from below through the floor and wall into the lid pegs.
// Pegs/holes on angled rows are vertical in world Z, not normal to the slope.
// EDGE_STYLE: "square" | "round" | "chamfer"   EDGE_MM radius/chamfer.
// Set COLS, ROWS, INNER_H, TILTS, NDEV, DEV_*, EDGE_* then include this file.
// Quality gates: python scripts/quality_gate.py --preset sliders-quads

include <devices.scad>

C_PITCH    = is_undef(PITCH)      ? 25.4 : PITCH;
C_COLS     = is_undef(COLS)       ? 5    : COLS;
C_ROWS     = is_undef(ROWS)       ? 4    : ROWS;
C_INNER    = is_undef(INNER_H)    ? 25   : INNER_H;
C_WALL     = is_undef(WALL)       ? 8.0  : WALL;
C_BOT      = is_undef(BOTTOM_T)   ? 3.0  : BOTTOM_T;
C_TOP      = is_undef(TOP_T)      ? 3.2  : TOP_T;
C_M3       = 3.3;
C_M3CS     = 6.6;
C_M3TAP    = 2.8;
C_FIT      = 0.40;   // per-side XY clearance, tray outer vs skirt inner
C_SKIRT    = 2.20;   // lid skirt thickness
C_SKIRT_H  = 8.00;   // how far the skirt hangs over the tray
C_PEG_H    = 2.50;   // alignment peg (short so the lid can drop on)
C_PEG_D    = 4.00;
C_SOCK_D   = 4.50;
C_SOCK_H   = 2.90;
C_PEG_INSET = 3.00;  // peg axis from the inner wall face (meat to the outer face)
C_MOUTH    = 1.00;   // extra inner opening at the skirt mouth (lead-in)
C_PART     = is_undef(PART)       ? "preview" : PART;
C_NDEV     = is_undef(NDEV)       ? 0 : NDEV;
C_NWALL    = is_undef(NWALL)      ? 0 : NWALL;
C_TILTS    = is_undef(TILTS)      ? [for (i=[0:C_ROWS-1]) 0] : TILTS;
C_EDGE     = is_undef(EDGE_STYLE) ? "round" : EDGE_STYLE;
C_EDGE_MM  = is_undef(EDGE_MM)    ? 2.0 : EDGE_MM;
C_HANG     = is_undef(HANG)       ? 1    : HANG;  // 1 = keyholes in the back wall
$fn = 28;

C_WALL_H = C_BOT + C_INNER;
C_EX     = C_FIT + C_SKIRT;

function tilt_of(i) = (len(C_TILTS) > i) ? C_TILTS[i] : 0;
function accum_y(i) = (i <= 0) ? 0 : accum_y(i-1) + C_PITCH * cos(tilt_of(i-1));
function accum_z(i) = (i <= 0) ? 0 : accum_z(i-1) + C_PITCH * sin(tilt_of(i-1));
function wy(i, ly) = accum_y(i) + ly * cos(tilt_of(i));
function wz(i, ly) = accum_z(i) + ly * sin(tilt_of(i));
// Lid-plane world XY/Z: rotate([tilt,0,0]) shifts Y by -z*sin(tilt).
function lid_wy(i, ly) = wy(i, ly) - C_WALL_H * sin(tilt_of(i));
function lid_wz(i, ly) = wz(i, ly) + C_WALL_H * cos(tilt_of(i));
function is_flat() = max([for (t = C_TILTS) abs(t)]) < 0.05;

module at_row(i, j=0, ty=0, tz=0) {
    if (j == i) {
        translate([0, ty, tz]) rotate([tilt_of(i), 0, 0]) children();
    } else if (j < C_ROWS) {
        a = tilt_of(j);
        at_row(i, j+1, ty + C_PITCH*cos(a), tz + C_PITCH*sin(a)) children();
    }
}

function case_w() = C_COLS*C_PITCH + 2*C_WALL;
function case_d() = C_ROWS*C_PITCH + 2*C_WALL;
function lid_w()  = case_w() + 2*C_EX;
function lid_d()  = case_d() + 2*C_EX;
function row_y0(i) = (i==0) ? -C_WALL : 0;
function row_ylen(i) = C_PITCH + (i==0?C_WALL:0) + (i==C_ROWS-1?C_WALL:0);

module edge_rect(w, h) {
    e = min(C_EDGE_MM, min(w,h)/2 - 0.2);
    if (C_EDGE == "round" && e > 0.2) {
        offset(r=e) offset(r=-e) square([w, h], center=false);
    } else if (C_EDGE == "chamfer" && e > 0.2) {
        hull() {
            translate([e, 0]) square([w-2*e, h], center=false);
            translate([0, e]) square([w, h-2*e], center=false);
        }
    } else {
        square([w, h], center=false);
    }
}

// Fastener XY is the lid-plane world XY so world-Z pegs meet the lid on slopes.
// Left/right pegs only on flat rows: a world-Z peg on a sloped row lands
// over the previous row's wall and blocks dropping the lid on.
module each_post() {
    ins = C_PEG_INSET;
    for (r = [0:C_ROWS-1]) {
        if (abs(tilt_of(r)) < 0.05) {
            y = lid_wy(r, C_PITCH/2);
            translate([-ins, y, 0]) children();
            translate([C_COLS*C_PITCH + ins, y, 0]) children();
        }
    }
    if (abs(tilt_of(0)) < 0.05) {
        yf = lid_wy(0, -ins);
        if (C_COLS > 1) {
            for (c = [1:C_COLS-1]) translate([c * C_PITCH, yf, 0]) children();
        } else {
            translate([C_PITCH/2, yf, 0]) children();
        }
    }
    if (abs(tilt_of(C_ROWS-1)) < 0.05) {
        yb = lid_wy(C_ROWS-1, C_PITCH + ins);
        if (C_COLS > 1) {
            for (c = [1:C_COLS-1]) translate([c * C_PITCH, yb, 0]) children();
        } else {
            translate([C_PITCH/2, yb, 0]) children();
        }
    }
}

module each_post_lid() {
    ins = C_PEG_INSET;
    for (r = [0:C_ROWS-1]) {
        if (abs(tilt_of(r)) < 0.05) {
            y = lid_wy(r, C_PITCH/2);
            z = lid_wz(r, C_PITCH/2);
            translate([-ins, y, z]) children();
            translate([C_COLS*C_PITCH + ins, y, z]) children();
        }
    }
    if (abs(tilt_of(0)) < 0.05) {
        yf = lid_wy(0, -ins);
        zf = lid_wz(0, -ins);
        if (C_COLS > 1) {
            for (c = [1:C_COLS-1]) translate([c * C_PITCH, yf, zf]) children();
        } else {
            translate([C_PITCH/2, yf, zf]) children();
        }
    }
    if (abs(tilt_of(C_ROWS-1)) < 0.05) {
        yb = lid_wy(C_ROWS-1, C_PITCH + ins);
        zb = lid_wz(C_ROWS-1, C_PITCH + ins);
        if (C_COLS > 1) {
            for (c = [1:C_COLS-1]) translate([c * C_PITCH, yb, zb]) children();
        } else {
            translate([C_PITCH/2, yb, zb]) children();
        }
    }
}

module m3_through() {
    cylinder(d=C_M3, h=400, center=true);
}

module m3_csink_floor() {
    translate([0, 0, -0.02]) cylinder(d1=C_M3CS, d2=C_M3, h=2.2);
}

module lid_peg_solid() {
    translate([0, 0, -C_PEG_H]) {
        cylinder(d=C_PEG_D, h=C_PEG_H + 0.2);
        cylinder(d1=C_PEG_D - 0.8, d2=C_PEG_D, h=0.7);
    }
}

module tray_socket() {
    translate([0, 0, -C_SOCK_H])
        cylinder(d=C_SOCK_D, h=C_SOCK_H + 0.4);
}

module row_outer_2d(i) {
    translate([-C_WALL, row_y0(i)])
        edge_rect(case_w(), row_ylen(i));
}

module row_lid_outer_2d(i) {
    y0 = row_y0(i) - (i==0 ? C_EX : 0);
    yl = row_ylen(i) + (i==0?C_EX:0) + (i==C_ROWS-1?C_EX:0);
    translate([-C_WALL - C_EX, y0])
        edge_rect(lid_w(), yl);
}

module row_skirt_inner_2d(i) {
    y0 = row_y0(i) - (i==0 ? C_FIT : 0);
    yl = row_ylen(i) + (i==0?C_FIT:0) + (i==C_ROWS-1?C_FIT:0);
    translate([-C_WALL - C_FIT, y0])
        edge_rect(case_w() + 2*C_FIT, yl);
}

module row_floor(i) {
    at_row(i)
        linear_extrude(C_BOT) row_outer_2d(i);
}

module row_walls(i) {
    at_row(i) difference() {
        linear_extrude(C_WALL_H) row_outer_2d(i);
        translate([0, 0, -0.1])
            linear_extrude(C_WALL_H + 0.2)
                square([C_COLS*C_PITCH, C_PITCH]);
    }
}

module side_kink_fill() {
    if (C_ROWS > 1)
        for (i = [0:C_ROWS-2]) {
            hull() {
                at_row(i) translate([-C_WALL, C_PITCH-0.05, 0])
                    cube([C_WALL, 0.05, C_WALL_H]);
                at_row(i+1) translate([-C_WALL, 0, 0])
                    cube([C_WALL, 0.05, C_WALL_H]);
            }
            hull() {
                at_row(i) translate([C_COLS*C_PITCH, C_PITCH-0.05, 0])
                    cube([C_WALL, 0.05, C_WALL_H]);
                at_row(i+1) translate([C_COLS*C_PITCH, 0, 0])
                    cube([C_WALL, 0.05, C_WALL_H]);
            }
            hull() {
                at_row(i) translate([-C_WALL, C_PITCH-0.05, 0])
                    cube([case_w(), 0.05, C_BOT]);
                at_row(i+1) translate([-C_WALL, 0, 0])
                    cube([case_w(), 0.05, C_BOT]);
            }
        }
}

module row_cavity(i) {
    at_row(i)
        translate([0, 0, C_BOT])
            cube([C_COLS*C_PITCH, C_PITCH, C_INNER + 1]);
}

module cavity_kink_fill() {
    if (C_ROWS > 1)
        for (i = [0:C_ROWS-2])
            hull() {
                at_row(i) translate([0, C_PITCH-0.05, C_BOT])
                    cube([C_COLS*C_PITCH, 0.05, C_INNER + 1]);
                at_row(i+1) translate([0, 0, C_BOT])
                    cube([C_COLS*C_PITCH, 0.05, C_INNER + 1]);
            }
}

function dev_place_is_bottom(id) = dev_is_bottom(id);

module at_device(id, c, r) {
    cx = (c + dev_cells_x(id)/2) * C_PITCH;
    cy = (r + dev_cells_y(id)/2) * C_PITCH;
    at_row(r)
        translate([cx, cy - r*C_PITCH, 0])
            children();
}

module wall_origin(side, pos) {
    r = min(C_ROWS-1, max(0, floor(pos)));
    ly = (pos - r + 0.5) * C_PITCH;
    if (side == "left")
        at_row(r) translate([-C_WALL, ly, C_BOT + C_INNER/2]) children();
    else if (side == "right")
        at_row(r) translate([C_COLS*C_PITCH + C_WALL, ly, C_BOT + C_INNER/2])
            rotate([0,0,180]) children();
    else if (side == "front")
        at_row(0) translate([(pos+0.5)*C_PITCH, -C_WALL, C_BOT + C_INNER/2])
            rotate([0,0,-90]) children();
    else
        at_row(C_ROWS-1) translate([(pos+0.5)*C_PITCH, C_PITCH + C_WALL, C_BOT + C_INNER/2])
            rotate([0,0,90]) children();
}

module wall_opening(side, id, pos) {
    wall_origin(side, pos) wall_cutout_of(id);
}

module wall_pocket(side, id, pos) {
    wall_origin(side, pos) difference() {
        translate([4, 0, 0]) cube([8, 22, 16], center=true);
        translate([4, 0, 0]) cube([6, 18, 12], center=true);
        wall_cutout_of(id);
    }
}

module tray_fasteners() {
    each_post() {
        m3_through();
        m3_csink_floor();
    }
    each_post_lid() tray_socket();
}

module wall_pocket_void(side, id, pos) {
    wall_origin(side, pos) translate([4, 0, 0]) cube([8, 22, 16], center=true);
}

module tray_wall_cuts() {
    if (C_NWALL > 0)
        for (i = [0:C_NWALL-1]) {
            wall_opening(WALL_SIDE[i], WALL_ID[i], WALL_POS[i]);
            wall_pocket_void(WALL_SIDE[i], WALL_ID[i], WALL_POS[i]);
        }
}

// Two keyholes through the back wall so the case hangs on screws.
// Head circle at the top; drop the case onto the screws, then down.
function hang_xs() =
    let (span = C_COLS * C_PITCH,
         inset = min(C_PITCH / 2, span / 2 - 6))
        (span > 28) ? [inset, span - inset] : [span / 2];

module hang_keyhole_2d() {
    hull() {
        translate([0, 7]) circle(d=8.5);
        translate([0, 3]) circle(d=4.2);
    }
    hull() {
        translate([0, 3]) circle(d=4.2);
        translate([0, -5]) circle(d=4.2);
    }
}

module hang_holes() {
    if (C_HANG)
        at_row(C_ROWS - 1)
            for (x = hang_xs())
                translate([x, C_PITCH + C_WALL / 2, C_WALL_H - 12])
                    rotate([90, 0, 0])
                        linear_extrude(C_WALL + 2, center=true)
                            hang_keyhole_2d();
}

module tray_extras() {
    if (C_NDEV > 0)
        for (i = [0:C_NDEV-1])
            if (dev_place_is_bottom(DEV_ID[i]))
                at_device(DEV_ID[i], DEV_C[i], DEV_R[i])
                    translate([0,0,C_BOT]) dev_bosses(DEV_ID[i]);
}

module bottom_tray_flat() {
    difference() {
        linear_extrude(C_WALL_H)
            translate([-C_WALL, -C_WALL]) edge_rect(case_w(), case_d());
        translate([0, 0, C_BOT])
            linear_extrude(C_WALL_H + 1)
                square([C_COLS*C_PITCH, C_ROWS*C_PITCH]);
        tray_fasteners();
        tray_wall_cuts();
        hang_holes();
    }
    tray_extras();
}

module bottom_tray_tilted() {
    difference() {
        union() {
            for (i = [0:C_ROWS-1]) {
                row_floor(i);
                row_walls(i);
            }
            side_kink_fill();
        }
        for (i = [0:C_ROWS-1]) row_cavity(i);
        cavity_kink_fill();
        tray_fasteners();
        tray_wall_cuts();
        hang_holes();
    }
    tray_extras();
}

module bottom_tray() {
    if (is_flat()) bottom_tray_flat();
    else bottom_tray_tilted();
}

module lid_device_bosses() {
    if (C_NDEV > 0)
        for (i = [0:C_NDEV-1])
            if (!dev_place_is_bottom(DEV_ID[i]))
                at_device(DEV_ID[i], DEV_C[i], DEV_R[i])
                    translate([0,0,C_WALL_H]) rotate([180,0,0])
                        dev_bosses(DEV_ID[i]);
}

module lid_device_cuts() {
    if (C_NDEV > 0)
        for (i = [0:C_NDEV-1])
            if (!dev_place_is_bottom(DEV_ID[i]))
                at_device(DEV_ID[i], DEV_C[i], DEV_R[i])
                    translate([0,0,C_WALL_H]) dev_cutouts(DEV_ID[i]);
}

module lid_pegs() {
    each_post_lid() lid_peg_solid();
}

module lid_tap_holes() {
    // From the peg up into the plate; stop short of the outer skin.
    each_post_lid()
        translate([0, 0, -C_PEG_H - 0.2])
            cylinder(d=C_M3TAP, h=C_PEG_H + C_TOP - 0.8);
}

module top_lid_flat() {
    difference() {
        union() {
            translate([0, 0, C_WALL_H])
                linear_extrude(C_TOP)
                    translate([-C_WALL - C_EX, -C_WALL - C_EX])
                        edge_rect(lid_w(), lid_d());
            translate([0, 0, C_WALL_H - C_SKIRT_H])
                linear_extrude(C_SKIRT_H)
                    difference() {
                        translate([-C_WALL - C_EX, -C_WALL - C_EX])
                            edge_rect(lid_w(), lid_d());
                        translate([-C_WALL - C_FIT, -C_WALL - C_FIT])
                            edge_rect(case_w() + 2*C_FIT, case_d() + 2*C_FIT);
                    }
            lid_pegs();
            lid_device_bosses();
        }
        // mouth lead-in: inner opening is 1 mm looser at the skirt lip
        translate([0, 0, C_WALL_H - C_SKIRT_H - 0.05])
            linear_extrude(1.5)
                translate([-C_WALL - C_FIT - C_MOUTH, -C_WALL - C_FIT - C_MOUTH])
                    square([case_w() + 2*(C_FIT + C_MOUTH),
                            case_d() + 2*(C_FIT + C_MOUTH)]);
        lid_device_cuts();
        lid_tap_holes();
    }
}

module row_lid(i) {
    at_row(i)
        translate([0, 0, C_WALL_H])
            linear_extrude(C_TOP) row_lid_outer_2d(i);
}

function lid_ly0(i) = row_y0(i) - (i==0 ? C_EX : 0);
function lid_ly1(i) = row_y0(i) + row_ylen(i) + (i==C_ROWS-1 ? C_EX : 0);

// Shoebox skirt hangs in world -Z so the lid can drop straight down
// onto a tilted tray. Local-Z skirts on a slope sweep in Y as they drop
// and eat C_FIT before the pegs engage.
module wz_skirt_post(x, ly_row, ly, z_off=0) {
    translate([x, lid_wy(ly_row, ly), lid_wz(ly_row, ly) - C_SKIRT_H + z_off])
        cube([C_SKIRT, 1.0, C_SKIRT_H]);
}

module world_z_side_skirts() {
    xl = -C_WALL - C_EX;
    xr = C_COLS*C_PITCH + C_WALL + C_FIT;
    for (i = [0:C_ROWS-1]) {
        hull() {
            wz_skirt_post(xl, i, lid_ly0(i));
            wz_skirt_post(xl, i, lid_ly1(i));
        }
        hull() {
            wz_skirt_post(xr, i, lid_ly0(i));
            wz_skirt_post(xr, i, lid_ly1(i));
        }
    }
    if (C_ROWS > 1)
        for (i = [0:C_ROWS-2]) {
            hull() {
                wz_skirt_post(xl, i, lid_ly1(i));
                wz_skirt_post(xl, i+1, lid_ly0(i+1));
            }
            hull() {
                wz_skirt_post(xr, i, lid_ly1(i));
                wz_skirt_post(xr, i+1, lid_ly0(i+1));
            }
        }
}

module world_z_end_skirts() {
    // Front and back: vertical strips at the lid's outer Y.
    yf = lid_wy(0, lid_ly0(0));
    zf = lid_wz(0, lid_ly0(0));
    translate([-C_WALL - C_EX, yf, zf - C_SKIRT_H])
        cube([lid_w(), C_SKIRT, C_SKIRT_H]);
    i = C_ROWS-1;
    yb = lid_wy(i, lid_ly1(i));
    zb = lid_wz(i, lid_ly1(i));
    translate([-C_WALL - C_EX, yb - C_SKIRT, zb - C_SKIRT_H])
        cube([lid_w(), C_SKIRT, C_SKIRT_H]);
}

module lid_kink_fill() {
    if (C_ROWS > 1)
        for (i = [0:C_ROWS-2]) {
            hull() {
                at_row(i) translate([-C_WALL - C_EX, C_PITCH-0.05, C_WALL_H])
                    cube([lid_w(), 0.05, C_TOP]);
                at_row(i+1) translate([-C_WALL - C_EX, 0, C_WALL_H])
                    cube([lid_w(), 0.05, C_TOP]);
            }
        }
}

module top_lid_tilted() {
    difference() {
        union() {
            for (i = [0:C_ROWS-1]) row_lid(i);
            lid_kink_fill();
            world_z_side_skirts();
            world_z_end_skirts();
            lid_pegs();
            lid_device_bosses();
        }
        lid_device_cuts();
        lid_tap_holes();
    }
}

module top_lid_use() {
    if (is_flat()) top_lid_flat();
    else top_lid_tilted();
}

function lid_print_z() =
    max([for (i = [0:C_ROWS-1])
        let (
            y0 = row_y0(i) - (i==0 ? C_EX : 0),
            y1 = row_y0(i) + row_ylen(i) + (i==C_ROWS-1 ? C_EX : 0)
        ) max(lid_wz(i, y0) + C_TOP, lid_wz(i, y1) + C_TOP)
    ]);

module top_lid_print() {
    rotate([180,0,0])
        translate([0, -case_d(), -lid_print_z()])
            top_lid_use();
}

module preview_assembly() {
    color([0.18,0.22,0.28]) bottom_tray();
    color([0.75,0.78,0.82], 0.92) top_lid_use();
}

module build_part() {
    if (C_PART == "bottom") bottom_tray();
    else if (C_PART == "top") top_lid_print();
    else if (C_PART == "top_use") top_lid_use();
    else preview_assembly();
}

build_part();
