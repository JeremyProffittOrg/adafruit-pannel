// Generated from library/devices.json. Do not edit by hand.
$fn = 24;

function dev_cells_x(id) =
  id == "empty" ? 1 :
  id == "neoslider" ? 1 :
  id == "quad_rotary" ? 1 :
  id == "rotary_qt" ? 1 :
  id == "ano" ? 2 :
  id == "oled_128x64" ? 2 :
  id == "tft_28" ? 4 :
  id == "t_display" ? 2 :
  id == "t_display_s3" ? 3 :
  id == "t_display_s3_touch" ? 3 :
  id == "t_display_s3_pro" ? 3 :
  id == "t_display_s3_amoled" ? 3 :
  id == "t_qt_pro" ? 2 :
  id == "t_hmi" ? 3 :
  id == "t_deck" ? 4 :
  id == "t_beam" ? 3 :
  id == "t_dongle_s3" ? 2 :
  id == "t_camera_s3" ? 2 :
  id == "m5_core" ? 3 :
  id == "m5_core2" ? 3 :
  id == "m5_module" ? 3 :
  id == "m5_module_13_2" ? 3 :
  id == "m5_stickc" ? 2 :
  id == "m5_atom" ? 1 :
  id == "m5_unit" ? 1 :
  id == "stemma_generic" ? 1 :
  id == "stemma_light" ? 1 :
  id == "stemma_tof" ? 1 :
  id == "stemma_pir" ? 1 :
  id == "stemma_env" ? 1 :
  id == "stemma_air" ? 2 :
  1;
function dev_cells_y(id) =
  id == "empty" ? 1 :
  id == "neoslider" ? 4 :
  id == "quad_rotary" ? 4 :
  id == "rotary_qt" ? 1 :
  id == "ano" ? 2 :
  id == "oled_128x64" ? 2 :
  id == "tft_28" ? 3 :
  id == "t_display" ? 1 :
  id == "t_display_s3" ? 1 :
  id == "t_display_s3_touch" ? 1 :
  id == "t_display_s3_pro" ? 3 :
  id == "t_display_s3_amoled" ? 1 :
  id == "t_qt_pro" ? 1 :
  id == "t_hmi" ? 2 :
  id == "t_deck" ? 3 :
  id == "t_beam" ? 1 :
  id == "t_dongle_s3" ? 1 :
  id == "t_camera_s3" ? 2 :
  id == "m5_core" ? 3 :
  id == "m5_core2" ? 3 :
  id == "m5_module" ? 3 :
  id == "m5_module_13_2" ? 3 :
  id == "m5_stickc" ? 1 :
  id == "m5_atom" ? 1 :
  id == "m5_unit" ? 1 :
  id == "stemma_generic" ? 1 :
  id == "stemma_light" ? 1 :
  id == "stemma_tof" ? 1 :
  id == "stemma_pir" ? 1 :
  id == "stemma_env" ? 1 :
  id == "stemma_air" ? 1 :
  1;
function dev_boss(id) =
  id == "empty" ? 6 :
  id == "neoslider" ? 6 :
  id == "quad_rotary" ? 6 :
  id == "rotary_qt" ? 6 :
  id == "ano" ? 6 :
  id == "oled_128x64" ? 4 :
  id == "tft_28" ? 4 :
  id == "t_display" ? 5 :
  id == "t_display_s3" ? 5 :
  id == "t_display_s3_touch" ? 5 :
  id == "t_display_s3_pro" ? 5 :
  id == "t_display_s3_amoled" ? 5 :
  id == "t_qt_pro" ? 5 :
  id == "t_hmi" ? 5 :
  id == "t_deck" ? 5 :
  id == "t_beam" ? 6 :
  id == "t_dongle_s3" ? 5 :
  id == "t_camera_s3" ? 5 :
  id == "m5_core" ? 6 :
  id == "m5_core2" ? 6 :
  id == "m5_module" ? 8 :
  id == "m5_module_13_2" ? 8 :
  id == "m5_stickc" ? 5 :
  id == "m5_atom" ? 5 :
  id == "m5_unit" ? 4 :
  id == "stemma_generic" ? 5 :
  id == "stemma_light" ? 4 :
  id == "stemma_tof" ? 4 :
  id == "stemma_pir" ? 4 :
  id == "stemma_env" ? 4 :
  id == "stemma_air" ? 4 :
  6;
function dev_is_bottom(id) =
  id == "empty" ? false :
  id == "neoslider" ? false :
  id == "quad_rotary" ? false :
  id == "rotary_qt" ? false :
  id == "ano" ? false :
  id == "oled_128x64" ? false :
  id == "tft_28" ? false :
  id == "t_display" ? false :
  id == "t_display_s3" ? false :
  id == "t_display_s3_touch" ? false :
  id == "t_display_s3_pro" ? false :
  id == "t_display_s3_amoled" ? false :
  id == "t_qt_pro" ? false :
  id == "t_hmi" ? false :
  id == "t_deck" ? false :
  id == "t_beam" ? true :
  id == "t_dongle_s3" ? true :
  id == "t_camera_s3" ? false :
  id == "m5_core" ? false :
  id == "m5_core2" ? false :
  id == "m5_module" ? true :
  id == "m5_module_13_2" ? true :
  id == "m5_stickc" ? false :
  id == "m5_atom" ? false :
  id == "m5_unit" ? false :
  id == "stemma_generic" ? true :
  id == "stemma_light" ? false :
  id == "stemma_tof" ? false :
  id == "stemma_pir" ? false :
  id == "stemma_env" ? false :
  id == "stemma_air" ? false :
  false;

module dev_cutouts(id) {
  if (id == "neoslider") {
    translate([0, 0, 9]) cube([4, 75, 20], center=true);
  }
  if (id == "quad_rotary") {
    translate([0, -28.575, -1]) cylinder(d=7.5, h=20);
    translate([0, -9.525, -1]) cylinder(d=7.5, h=20);
    translate([0, 9.525, -1]) cylinder(d=7.5, h=20);
    translate([0, 28.575, -1]) cylinder(d=7.5, h=20);
  }
  if (id == "rotary_qt") {
    translate([0, 0, -1]) cylinder(d=7.5, h=20);
  }
  if (id == "ano") {
    translate([0, 0, -1]) cylinder(d=22, h=20);
  }
  if (id == "oled_128x64") {
    translate([0, 0, 9]) cube([30, 16, 20], center=true);
  }
  if (id == "tft_28") {
    translate([0, 0, 9]) cube([69.6, 45.2, 20], center=true);
  }
  if (id == "t_display") {
    translate([0, 0, 9]) cube([28, 14, 20], center=true);
  }
  if (id == "t_display_s3") {
    translate([0, 0, 9]) cube([42, 18, 20], center=true);
  }
  if (id == "t_display_s3_touch") {
    translate([0, 0, 9]) cube([42, 18, 20], center=true);
  }
  if (id == "t_display_s3_pro") {
    translate([0, 0, 9]) cube([48, 28, 20], center=true);
  }
  if (id == "t_display_s3_amoled") {
    translate([0, 0, 9]) cube([44, 18, 20], center=true);
  }
  if (id == "t_qt_pro") {
    translate([0, 0, 9]) cube([16, 16, 20], center=true);
  }
  if (id == "t_hmi") {
    translate([0, 0, 9]) cube([56, 42, 20], center=true);
  }
  if (id == "t_deck") {
    translate([0, 10, 9]) cube([50, 32, 20], center=true);
  }
  if (id == "t_dongle_s3") {
    translate([8, 0, 9]) cube([12, 12, 20], center=true);
  }
  if (id == "t_camera_s3") {
    translate([0, 0, -1]) cylinder(d=8, h=20);
  }
  if (id == "m5_core") {
    translate([0, 4, 9]) cube([40, 32, 20], center=true);
  }
  if (id == "m5_core2") {
    translate([0, 2, 9]) cube([42, 34, 20], center=true);
  }
  if (id == "m5_stickc") {
    translate([6, 0, 9]) cube([22, 12, 20], center=true);
  }
  if (id == "m5_atom") {
    translate([0, 0, 9]) cube([14, 14, 20], center=true);
  }
  if (id == "m5_unit") {
    translate([0, 0, -1]) cylinder(d=8, h=20);
  }
  if (id == "stemma_light") {
    translate([0, 0, -1]) cylinder(d=5, h=20);
  }
  if (id == "stemma_tof") {
    translate([0, 0, -1]) cylinder(d=8, h=20);
  }
  if (id == "stemma_pir") {
    translate([0, 0, -1]) cylinder(d=12, h=20);
  }
  if (id == "stemma_env") {
    for (gy = [-3, 0, 3])
      translate([0, 0+gy, 9]) cube([12, 1.4, 20], center=true);
  }
  if (id == "stemma_air") {
    for (gy = [-3, 0, 3])
      translate([0, 0+gy, 9]) cube([16, 1.4, 20], center=true);
  }
}

module dev_bosses(id) {
  if (id == "neoslider") {
    translate([8.255, 19.05, 0]) difference() {
      cylinder(d=6.8, h=6);
      translate([0,0,-0.2]) cylinder(d=2.30, h=6+0.4);
    }
    translate([-8.255, 19.05, 0]) difference() {
      cylinder(d=6.8, h=6);
      translate([0,0,-0.2]) cylinder(d=2.30, h=6+0.4);
    }
    translate([8.255, -19.05, 0]) difference() {
      cylinder(d=6.8, h=6);
      translate([0,0,-0.2]) cylinder(d=2.30, h=6+0.4);
    }
    translate([-8.255, -19.05, 0]) difference() {
      cylinder(d=6.8, h=6);
      translate([0,0,-0.2]) cylinder(d=2.30, h=6+0.4);
    }
  }
  if (id == "quad_rotary") {
    translate([8.255, 19.05, 0]) difference() {
      cylinder(d=6.8, h=6);
      translate([0,0,-0.2]) cylinder(d=2.30, h=6+0.4);
    }
    translate([-8.255, 19.05, 0]) difference() {
      cylinder(d=6.8, h=6);
      translate([0,0,-0.2]) cylinder(d=2.30, h=6+0.4);
    }
    translate([8.255, -19.05, 0]) difference() {
      cylinder(d=6.8, h=6);
      translate([0,0,-0.2]) cylinder(d=2.30, h=6+0.4);
    }
    translate([-8.255, -19.05, 0]) difference() {
      cylinder(d=6.8, h=6);
      translate([0,0,-0.2]) cylinder(d=2.30, h=6+0.4);
    }
  }
  if (id == "rotary_qt") {
    translate([10.16, 10.16, 0]) difference() {
      cylinder(d=6.8, h=6);
      translate([0,0,-0.2]) cylinder(d=2.30, h=6+0.4);
    }
    translate([-10.16, 10.16, 0]) difference() {
      cylinder(d=6.8, h=6);
      translate([0,0,-0.2]) cylinder(d=2.30, h=6+0.4);
    }
    translate([10.16, -10.16, 0]) difference() {
      cylinder(d=6.8, h=6);
      translate([0,0,-0.2]) cylinder(d=2.30, h=6+0.4);
    }
    translate([-10.16, -10.16, 0]) difference() {
      cylinder(d=6.8, h=6);
      translate([0,0,-0.2]) cylinder(d=2.30, h=6+0.4);
    }
  }
  if (id == "ano") {
    translate([15.24, 17.78, 0]) difference() {
      cylinder(d=6.8, h=6);
      translate([0,0,-0.2]) cylinder(d=2.30, h=6+0.4);
    }
    translate([-15.24, 17.78, 0]) difference() {
      cylinder(d=6.8, h=6);
      translate([0,0,-0.2]) cylinder(d=2.30, h=6+0.4);
    }
    translate([15.24, -17.78, 0]) difference() {
      cylinder(d=6.8, h=6);
      translate([0,0,-0.2]) cylinder(d=2.30, h=6+0.4);
    }
    translate([-15.24, -17.78, 0]) difference() {
      cylinder(d=6.8, h=6);
      translate([0,0,-0.2]) cylinder(d=2.30, h=6+0.4);
    }
  }
  if (id == "oled_128x64") {
    translate([15, 14, 0]) difference() {
      cylinder(d=6.8, h=4);
      translate([0,0,-0.2]) cylinder(d=2.30, h=4+0.4);
    }
    translate([-15, 14, 0]) difference() {
      cylinder(d=6.8, h=4);
      translate([0,0,-0.2]) cylinder(d=2.30, h=4+0.4);
    }
    translate([15, -14, 0]) difference() {
      cylinder(d=6.8, h=4);
      translate([0,0,-0.2]) cylinder(d=2.30, h=4+0.4);
    }
    translate([-15, -14, 0]) difference() {
      cylinder(d=6.8, h=4);
      translate([0,0,-0.2]) cylinder(d=2.30, h=4+0.4);
    }
  }
  if (id == "tft_28") {
    translate([38.1, 28.6, 0]) difference() {
      cylinder(d=6.8, h=4);
      translate([0,0,-0.2]) cylinder(d=2.30, h=4+0.4);
    }
    translate([-38.1, 28.6, 0]) difference() {
      cylinder(d=6.8, h=4);
      translate([0,0,-0.2]) cylinder(d=2.30, h=4+0.4);
    }
    translate([38.1, -28.6, 0]) difference() {
      cylinder(d=6.8, h=4);
      translate([0,0,-0.2]) cylinder(d=2.30, h=4+0.4);
    }
    translate([-38.1, -28.6, 0]) difference() {
      cylinder(d=6.8, h=4);
      translate([0,0,-0.2]) cylinder(d=2.30, h=4+0.4);
    }
  }
  if (id == "t_display") {
    translate([20, 8, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
    translate([-20, 8, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
    translate([20, -8, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
    translate([-20, -8, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
  }
  if (id == "t_display_s3") {
    translate([24, 8, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
    translate([-24, 8, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
    translate([24, -8, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
    translate([-24, -8, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
  }
  if (id == "t_display_s3_touch") {
    translate([24, 8, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
    translate([-24, 8, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
    translate([24, -8, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
    translate([-24, -8, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
  }
  if (id == "t_display_s3_pro") {
    translate([22, 22, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
    translate([-22, 22, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
    translate([22, -22, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
    translate([-22, -22, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
  }
  if (id == "t_display_s3_amoled") {
    translate([23, 8, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
    translate([-23, 8, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
    translate([23, -8, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
    translate([-23, -8, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
  }
  if (id == "t_qt_pro") {
    translate([12, 6, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
    translate([-12, 6, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
    translate([12, -6, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
    translate([-12, -6, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
  }
  if (id == "t_hmi") {
    translate([28, 18, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
    translate([-28, 18, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
    translate([28, -18, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
    translate([-28, -18, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
  }
  if (id == "t_deck") {
    translate([40, 28, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.30, h=5+0.4);
    }
    translate([-40, 28, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.30, h=5+0.4);
    }
    translate([40, -28, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.30, h=5+0.4);
    }
    translate([-40, -28, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.30, h=5+0.4);
    }
  }
  if (id == "t_beam") {
    translate([25, 8, 0]) difference() {
      cylinder(d=6.8, h=6);
      translate([0,0,-0.2]) cylinder(d=2.00, h=6+0.4);
    }
    translate([-25, 8, 0]) difference() {
      cylinder(d=6.8, h=6);
      translate([0,0,-0.2]) cylinder(d=2.00, h=6+0.4);
    }
    translate([25, -8, 0]) difference() {
      cylinder(d=6.8, h=6);
      translate([0,0,-0.2]) cylinder(d=2.00, h=6+0.4);
    }
    translate([-25, -8, 0]) difference() {
      cylinder(d=6.8, h=6);
      translate([0,0,-0.2]) cylinder(d=2.00, h=6+0.4);
    }
  }
  if (id == "t_dongle_s3") {
    translate([12, 5, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
    translate([-12, 5, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
  }
  if (id == "t_camera_s3") {
    translate([14, 10, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
    translate([-14, 10, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
    translate([14, -10, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
    translate([-14, -10, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
  }
  if (id == "m5_core") {
    translate([19, 19, 0]) difference() {
      cylinder(d=8.0, h=6);
      translate([0,0,-0.2]) cylinder(d=3.00, h=6+0.4);
    }
    translate([-19, 19, 0]) difference() {
      cylinder(d=8.0, h=6);
      translate([0,0,-0.2]) cylinder(d=3.00, h=6+0.4);
    }
    translate([19, -19, 0]) difference() {
      cylinder(d=8.0, h=6);
      translate([0,0,-0.2]) cylinder(d=3.00, h=6+0.4);
    }
    translate([-19, -19, 0]) difference() {
      cylinder(d=8.0, h=6);
      translate([0,0,-0.2]) cylinder(d=3.00, h=6+0.4);
    }
  }
  if (id == "m5_core2") {
    translate([19, 19, 0]) difference() {
      cylinder(d=8.0, h=6);
      translate([0,0,-0.2]) cylinder(d=3.00, h=6+0.4);
    }
    translate([-19, 19, 0]) difference() {
      cylinder(d=8.0, h=6);
      translate([0,0,-0.2]) cylinder(d=3.00, h=6+0.4);
    }
    translate([19, -19, 0]) difference() {
      cylinder(d=8.0, h=6);
      translate([0,0,-0.2]) cylinder(d=3.00, h=6+0.4);
    }
    translate([-19, -19, 0]) difference() {
      cylinder(d=8.0, h=6);
      translate([0,0,-0.2]) cylinder(d=3.00, h=6+0.4);
    }
  }
  if (id == "m5_module") {
    translate([19, 19, 0]) difference() {
      cylinder(d=8.0, h=8);
      translate([0,0,-0.2]) cylinder(d=3.00, h=8+0.4);
    }
    translate([-19, 19, 0]) difference() {
      cylinder(d=8.0, h=8);
      translate([0,0,-0.2]) cylinder(d=3.00, h=8+0.4);
    }
    translate([19, -19, 0]) difference() {
      cylinder(d=8.0, h=8);
      translate([0,0,-0.2]) cylinder(d=3.00, h=8+0.4);
    }
    translate([-19, -19, 0]) difference() {
      cylinder(d=8.0, h=8);
      translate([0,0,-0.2]) cylinder(d=3.00, h=8+0.4);
    }
  }
  if (id == "m5_module_13_2") {
    translate([19, 19, 0]) difference() {
      cylinder(d=8.0, h=8);
      translate([0,0,-0.2]) cylinder(d=3.00, h=8+0.4);
    }
    translate([-19, 19, 0]) difference() {
      cylinder(d=8.0, h=8);
      translate([0,0,-0.2]) cylinder(d=3.00, h=8+0.4);
    }
    translate([19, -19, 0]) difference() {
      cylinder(d=8.0, h=8);
      translate([0,0,-0.2]) cylinder(d=3.00, h=8+0.4);
    }
    translate([-19, -19, 0]) difference() {
      cylinder(d=8.0, h=8);
      translate([0,0,-0.2]) cylinder(d=3.00, h=8+0.4);
    }
  }
  if (id == "m5_stickc") {
    translate([18, 5, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
    translate([-18, 5, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
  }
  if (id == "m5_atom") {
    translate([8, 8, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
    translate([-8, 8, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
    translate([8, -8, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
    translate([-8, -8, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.00, h=5+0.4);
    }
  }
  if (id == "m5_unit") {
    translate([8, 8, 0]) difference() {
      cylinder(d=6.8, h=4);
      translate([0,0,-0.2]) cylinder(d=2.00, h=4+0.4);
    }
    translate([-8, 8, 0]) difference() {
      cylinder(d=6.8, h=4);
      translate([0,0,-0.2]) cylinder(d=2.00, h=4+0.4);
    }
    translate([8, -8, 0]) difference() {
      cylinder(d=6.8, h=4);
      translate([0,0,-0.2]) cylinder(d=2.00, h=4+0.4);
    }
    translate([-8, -8, 0]) difference() {
      cylinder(d=6.8, h=4);
      translate([0,0,-0.2]) cylinder(d=2.00, h=4+0.4);
    }
  }
  if (id == "stemma_generic") {
    translate([10.16, 0, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.30, h=5+0.4);
    }
    translate([-10.16, 0, 0]) difference() {
      cylinder(d=6.8, h=5);
      translate([0,0,-0.2]) cylinder(d=2.30, h=5+0.4);
    }
  }
  if (id == "stemma_light") {
    translate([10.16, 0, 0]) difference() {
      cylinder(d=6.8, h=4);
      translate([0,0,-0.2]) cylinder(d=2.30, h=4+0.4);
    }
    translate([-10.16, 0, 0]) difference() {
      cylinder(d=6.8, h=4);
      translate([0,0,-0.2]) cylinder(d=2.30, h=4+0.4);
    }
  }
  if (id == "stemma_tof") {
    translate([10.16, 0, 0]) difference() {
      cylinder(d=6.8, h=4);
      translate([0,0,-0.2]) cylinder(d=2.30, h=4+0.4);
    }
    translate([-10.16, 0, 0]) difference() {
      cylinder(d=6.8, h=4);
      translate([0,0,-0.2]) cylinder(d=2.30, h=4+0.4);
    }
  }
  if (id == "stemma_pir") {
    translate([10.16, 10.16, 0]) difference() {
      cylinder(d=6.8, h=4);
      translate([0,0,-0.2]) cylinder(d=2.30, h=4+0.4);
    }
    translate([-10.16, 10.16, 0]) difference() {
      cylinder(d=6.8, h=4);
      translate([0,0,-0.2]) cylinder(d=2.30, h=4+0.4);
    }
    translate([10.16, -10.16, 0]) difference() {
      cylinder(d=6.8, h=4);
      translate([0,0,-0.2]) cylinder(d=2.30, h=4+0.4);
    }
    translate([-10.16, -10.16, 0]) difference() {
      cylinder(d=6.8, h=4);
      translate([0,0,-0.2]) cylinder(d=2.30, h=4+0.4);
    }
  }
  if (id == "stemma_env") {
    translate([10.16, 0, 0]) difference() {
      cylinder(d=6.8, h=4);
      translate([0,0,-0.2]) cylinder(d=2.30, h=4+0.4);
    }
    translate([-10.16, 0, 0]) difference() {
      cylinder(d=6.8, h=4);
      translate([0,0,-0.2]) cylinder(d=2.30, h=4+0.4);
    }
  }
  if (id == "stemma_air") {
    translate([12, 6, 0]) difference() {
      cylinder(d=6.8, h=4);
      translate([0,0,-0.2]) cylinder(d=2.30, h=4+0.4);
    }
    translate([-12, 6, 0]) difference() {
      cylinder(d=6.8, h=4);
      translate([0,0,-0.2]) cylinder(d=2.30, h=4+0.4);
    }
  }
}

module wall_cutout_of(id) {
  if (id == "m5_unit") {
    rotate([0,90,0]) cylinder(d=8, h=20, center=true);
  }
  if (id == "stemma_light") {
    rotate([0,90,0]) cylinder(d=5, h=20, center=true);
  }
  if (id == "stemma_tof") {
    rotate([0,90,0]) cylinder(d=8, h=20, center=true);
  }
  if (id == "stemma_pir") {
    rotate([0,90,0]) cylinder(d=12, h=20, center=true);
  }
  if (id == "stemma_env") {
    for (gy = [-3, 0, 3])
      translate([0, gy, 0]) cube([20, 12, 1.4], center=true);
  }
  if (id == "stemma_air") {
    for (gy = [-3, 0, 3])
      translate([0, gy, 0]) cube([20, 16, 1.4], center=true);
  }
}

