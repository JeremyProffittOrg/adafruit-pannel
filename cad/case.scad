// First-class two-piece 1.00 in control case (YAPP-style shell).
// Closed tray: floor + left + right + front + back walls.
// Lid posts hang from the BACK of the lid, in the wall rim, world-Z (straight down).
// Pegs/holes on angled rows are vertical in world Z, not normal to the slope.
// EDGE_STYLE: "square" | "round" | "chamfer"   EDGE_MM radius/chamfer.
// Set COLS, ROWS, INNER_H, TILTS, NDEV, DEV_*, EDGE_* then include this file.

include <devices.scad>

C_PITCH    = is_undef(PITCH)      ? 25.4 : PITCH;
C_COLS     = is_undef(COLS)       ? 5    : COLS;
C_ROWS     = is_undef(ROWS)       ? 4    : ROWS;
C_INNER    = is_undef(INNER_H)    ? 25   : INNER_H;
C_WALL     = is_undef(WALL)       ? 8.0  : WALL;
C_BOT      = is_undef(BOTTOM_T)   ? 3.0  : BOTTOM_T;
C_TOP      = is_undef(TOP_T)      ? 3.2  : TOP_T;
C_REBATE   = 1.6;
C_M3       = 3.3;
C_M3CS     = 6.6;
C_POST     = 6.8;
C_PART     = is_undef(PART)       ? "preview" : PART;
C_NDEV     = is_undef(NDEV)       ? 0 : NDEV;
C_NWALL    = is_undef(NWALL)      ? 0 : NWALL;
C_TILTS    = is_undef(TILTS)      ? [for (i=[0:C_ROWS-1]) 0] : TILTS;
C_EDGE     = is_undef(EDGE_STYLE) ? "round" : EDGE_STYLE;
C_EDGE_MM  = is_undef(EDGE_MM)    ? 2.0 : EDGE_MM;
$fn = 28;

H_CASE = C_BOT + C_INNER + C_REBATE;

function tilt_of(i) = (len(C_TILTS) > i) ? C_TILTS[i] : 0;
function accum_y(i) = (i <= 0) ? 0 : accum_y(i-1) + C_PITCH * cos(tilt_of(i-1));
function accum_z(i) = (i <= 0) ? 0 : accum_z(i-1) + C_PITCH * sin(tilt_of(i-1));
function wy(i, ly) = accum_y(i) + ly * cos(tilt_of(i));
function wz(i, ly) = accum_z(i) + ly * sin(tilt_of(i));

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

// World-Z posts on 25.4 mm pitch, in the WALL, never in the cell grid.
module each_post() {
    xs = [-C_WALL/2, C_COLS*C_PITCH + C_WALL/2];
    // left and right walls: one post at each row boundary (straight down)
    for (r = [0:C_ROWS]) {
        i  = (r == C_ROWS) ? C_ROWS-1 : r;
        ly = (r == C_ROWS) ? C_PITCH : 0;
        y  = wy(i, ly);
        for (x = xs) translate([x, y, 0]) children();
    }
    // front wall (row 0, ly = -WALL/2)
    yf = wy(0, -C_WALL/2);
    for (c = [0:C_COLS]) {
        x = (c == 0) ? -C_WALL/2 :
            (c == C_COLS) ? C_COLS*C_PITCH + C_WALL/2 :
            c * C_PITCH;
        translate([x, yf, 0]) children();
    }
    // back wall (last row, ly = PITCH+WALL/2)
    yb = wy(C_ROWS-1, C_PITCH + C_WALL/2);
    for (c = [1:C_COLS-1])
        translate([c * C_PITCH, yb, 0]) children();
}

module world_z_hole() {
    cylinder(d=C_M3, h=400, center=true);
    translate([0,0,-1]) cylinder(d1=C_M3CS, d2=C_M3, h=2);
}

module world_z_socket() {
    cylinder(d=C_POST+0.45, h=400, center=true);
}

module world_z_lid_post() {
    difference() {
        cylinder(d=C_POST, h=H_CASE+20);
        translate([0,0,-0.2]) cylinder(d=2.8, h=H_CASE+21);
    }
}

module row_outer_2d(i) {
    translate([-C_WALL, row_y0(i)])
        edge_rect(case_w(), row_ylen(i));
}

module row_floor(i) {
    at_row(i)
        linear_extrude(C_BOT) row_outer_2d(i);
}

module row_walls(i) {
    at_row(i) difference() {
        linear_extrude(H_CASE) row_outer_2d(i);
        translate([0, 0, -0.1])
            linear_extrude(H_CASE + 0.2)
                square([C_COLS*C_PITCH, C_PITCH]);
    }
}

module side_kink_fill() {
    if (C_ROWS > 1)
        for (i = [0:C_ROWS-2]) {
            hull() {
                at_row(i) translate([-C_WALL, C_PITCH-0.05, 0])
                    cube([C_WALL, 0.05, H_CASE]);
                at_row(i+1) translate([-C_WALL, 0, 0])
                    cube([C_WALL, 0.05, H_CASE]);
            }
            hull() {
                at_row(i) translate([C_COLS*C_PITCH, C_PITCH-0.05, 0])
                    cube([C_WALL, 0.05, H_CASE]);
                at_row(i+1) translate([C_COLS*C_PITCH, 0, 0])
                    cube([C_WALL, 0.05, H_CASE]);
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
            cube([C_COLS*C_PITCH, C_PITCH, C_INNER + C_REBATE + 1]);
}

module cavity_kink_fill() {
    if (C_ROWS > 1)
        for (i = [0:C_ROWS-2])
            hull() {
                at_row(i) translate([0, C_PITCH-0.05, C_BOT])
                    cube([C_COLS*C_PITCH, 0.05, C_INNER + C_REBATE + 1]);
                at_row(i+1) translate([0, 0, C_BOT])
                    cube([C_COLS*C_PITCH, 0.05, C_INNER + C_REBATE + 1]);
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
    if (side == "left")
        translate([-C_WALL, (pos+0.5)*C_PITCH, C_BOT + C_INNER/2]) children();
    else if (side == "right")
        translate([C_COLS*C_PITCH + C_WALL, (pos+0.5)*C_PITCH, C_BOT + C_INNER/2])
            rotate([0,0,180]) children();
    else if (side == "front")
        translate([(pos+0.5)*C_PITCH, -C_WALL, C_BOT + C_INNER/2])
            rotate([0,0,-90]) children();
    else
        translate([(pos+0.5)*C_PITCH, C_ROWS*C_PITCH + C_WALL, C_BOT + C_INNER/2])
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

module bottom_tray() {
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
        each_post() {
            world_z_hole();
            world_z_socket();
        }
        if (C_NWALL > 0)
            for (i = [0:C_NWALL-1])
                wall_opening(WALL_SIDE[i], WALL_ID[i], WALL_POS[i]);
    }
    if (C_NWALL > 0)
        for (i = [0:C_NWALL-1])
            wall_pocket(WALL_SIDE[i], WALL_ID[i], WALL_POS[i]);
    if (C_NDEV > 0)
        for (i = [0:C_NDEV-1])
            if (dev_place_is_bottom(DEV_ID[i]))
                at_device(DEV_ID[i], DEV_C[i], DEV_R[i])
                    translate([0,0,C_BOT]) dev_bosses(DEV_ID[i]);
}

module row_lid(i) {
    at_row(i)
        translate([0, 0, C_BOT + C_INNER])
            linear_extrude(C_TOP) row_outer_2d(i);
}

module lid_kink_fill() {
    if (C_ROWS > 1)
        for (i = [0:C_ROWS-2])
            hull() {
                at_row(i) translate([-C_WALL, C_PITCH-0.05, C_BOT + C_INNER])
                    cube([case_w(), 0.05, C_TOP]);
                at_row(i+1) translate([-C_WALL, 0, C_BOT + C_INNER])
                    cube([case_w(), 0.05, C_TOP]);
            }
}

module top_lid_use() {
    z0 = C_BOT + C_INNER;
    difference() {
        union() {
            for (i = [0:C_ROWS-1]) row_lid(i);
            lid_kink_fill();
            // posts hang straight down in world Z, in the rim, never in a cell
            each_post()
                translate([0, 0, C_BOT + 0.2])
                    difference() {
                        cylinder(d=C_POST, h=C_INNER - 0.2);
                        translate([0,0,-0.1]) cylinder(d=2.8, h=C_INNER);
                    }
            if (C_NDEV > 0)
                for (i = [0:C_NDEV-1])
                    if (!dev_place_is_bottom(DEV_ID[i]))
                        at_device(DEV_ID[i], DEV_C[i], DEV_R[i])
                            translate([0,0,z0]) rotate([180,0,0])
                                dev_bosses(DEV_ID[i]);
        }
        if (C_NDEV > 0)
            for (i = [0:C_NDEV-1])
                if (!dev_place_is_bottom(DEV_ID[i]))
                    at_device(DEV_ID[i], DEV_C[i], DEV_R[i])
                        translate([0,0,z0]) dev_cutouts(DEV_ID[i]);
        each_post()
            translate([0,0,0]) cylinder(d=2.8, h=400, center=true);
    }
}

module top_lid_print() {
    z0 = C_BOT + C_INNER;
    rotate([180,0,0])
        translate([0, -case_d(), -(z0 + C_TOP)])
            top_lid_use();
}

module preview_assembly() {
    color([0.18,0.22,0.28]) bottom_tray();
    color([0.75,0.78,0.82], 0.92) top_lid_use();
}

module build_part() {
    if (C_PART == "bottom") bottom_tray();
    else if (C_PART == "top") top_lid_print();
    else preview_assembly();
}

build_part();
