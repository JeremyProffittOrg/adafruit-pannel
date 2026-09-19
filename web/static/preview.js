import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const PITCH = 25.4;
const WALL = 8;
const BOT = 3;
const TOP = 3.2;
const FIT = 0.4;
const SKIRT = 2.2;
const SKIRT_H = 8;
const PEG_H = 2.5;
const PEG_D = 4;
const PEG_INSET = 3;
const EX = FIT + SKIRT;
const CUT = 0xff4d6d; // high-contrast cutout fill (YAPP-style lid holes)

let renderer, scene, camera, controls, root;
let viewMode = "assembly";

function layout() {
  return window.PANEL_LAYOUT;
}
function byId() {
  return window.PANEL_BY_ID || {};
}
function tiltOf(l, i) {
  return (l.tilts && l.tilts[i]) || 0;
}
function accumY(l, i) {
  let y = 0;
  for (let j = 0; j < i; j++) y += PITCH * Math.cos((tiltOf(l, j) * Math.PI) / 180);
  return y;
}
function accumZ(l, i) {
  let z = 0;
  for (let j = 0; j < i; j++) z += PITCH * Math.sin((tiltOf(l, j) * Math.PI) / 180);
  return z;
}

function roundedRectPath(shape, x, y, w, h, r) {
  r = Math.max(0, Math.min(r, w / 2, h / 2));
  shape.moveTo(x + r, y);
  shape.lineTo(x + w - r, y);
  shape.quadraticCurveTo(x + w, y, x + w, y + r);
  shape.lineTo(x + w, y + h - r);
  shape.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  shape.lineTo(x + r, y + h);
  shape.quadraticCurveTo(x, y + h, x, y + h - r);
  shape.lineTo(x, y + r);
  shape.quadraticCurveTo(x, y, x + r, y);
}

function holePath(cut) {
  const p = new THREE.Path();
  const x = cut.x || 0;
  const y = cut.y || 0;
  if (cut.type === "hole") {
    const r = (cut.d || 8) / 2;
    p.absarc(x, y, r, 0, Math.PI * 2, true);
  } else if (cut.type === "slot") {
    const w = cut.w || 4;
    const len = cut.l || 20;
    roundedRectPath(p, x - w / 2, y - len / 2, w, len, Math.min(w, len) / 2);
  } else if (cut.type === "window") {
    const w = cut.w || 20;
    const h = cut.h || 12;
    roundedRectPath(p, x - w / 2, y - h / 2, w, h, 1.2);
  } else if (cut.type === "grill") {
    const w = cut.w || 12;
    const h = cut.h || 8;
    roundedRectPath(p, x - w / 2, y - h / 2, w, h, 0.6);
  }
  return p;
}

function deviceCenter(placed, def) {
  return {
    x: (placed.c + def.cells_x / 2) * PITCH,
    y: (placed.r + def.cells_y / 2) * PITCH,
  };
}

function placedDevices(l) {
  const lib = byId();
  return (l.devices || [])
    .map((p) => ({ p, def: lib[p.id] }))
    .filter((x) => x.def && x.def.place !== "none");
}

function addCutoutMarkers(parent, cx, cy, z, cuts, rotX) {
  const mat = new THREE.MeshBasicMaterial({ color: CUT, side: THREE.DoubleSide });
  for (const cut of cuts || []) {
    const x = cx + (cut.x || 0);
    const y = cy + (cut.y || 0);
    let mesh;
    if (cut.type === "hole") {
      mesh = new THREE.Mesh(new THREE.CylinderGeometry((cut.d || 8) / 2, (cut.d || 8) / 2, TOP + 1.2, 24), mat);
      mesh.rotation.x = Math.PI / 2;
    } else if (cut.type === "slot") {
      mesh = new THREE.Mesh(new THREE.BoxGeometry(cut.w || 4, cut.l || 20, TOP + 1.2), mat);
    } else if (cut.type === "window") {
      mesh = new THREE.Mesh(new THREE.BoxGeometry(cut.w || 20, cut.h || 12, TOP + 1.2), mat);
    } else if (cut.type === "grill") {
      const g = new THREE.Group();
      for (const gy of [-3, 0, 3]) {
        const sl = new THREE.Mesh(new THREE.BoxGeometry(cut.w || 12, 1.6, TOP + 1.2), mat);
        sl.position.y = gy;
        g.add(sl);
      }
      g.position.set(x, y, z);
      if (rotX) g.rotation.x = rotX;
      parent.add(g);
      continue;
    } else continue;
    mesh.position.set(x, y, z);
    if (rotX) mesh.rotation.x += rotX;
    parent.add(mesh);
  }
}

function lidWithHoles(l, inner) {
  const cols = l.cols;
  const rows = l.rows;
  const w = cols * PITCH + 2 * WALL + 2 * EX;
  const d = rows * PITCH + 2 * WALL + 2 * EX;
  const shape = new THREE.Shape();
  const e = Math.min(l.edge_mm || 2, 6);
  roundedRectPath(shape, -WALL - EX, -WALL - EX, w, d, l.edge_style === "square" ? 0 : e);

  for (const { p, def } of placedDevices(l)) {
    if (def.place === "bottom" || def.place === "wall") continue;
    const c = deviceCenter(p, def);
    for (const cut of def.cutouts || []) {
      const hp = holePath(cut);
      // offset hole path by device center
      const shifted = new THREE.Path();
      const pts = hp.getPoints(24);
      if (!pts.length) continue;
      shifted.moveTo(pts[0].x + c.x, pts[0].y + c.y);
      for (let i = 1; i < pts.length; i++) shifted.lineTo(pts[i].x + c.x, pts[i].y + c.y);
      shifted.autoClose = true;
      shape.holes.push(shifted);
    }
  }

  const geo = new THREE.ExtrudeGeometry(shape, { depth: TOP, bevelEnabled: false, curveSegments: 12 });
  const mesh = new THREE.Mesh(
    geo,
    new THREE.MeshLambertMaterial({ color: 0xd6dee8, side: THREE.DoubleSide })
  );
  mesh.position.z = BOT + inner;
  return mesh;
}

function build(l) {
  const g = new THREE.Group();
  if (!l) return g;
  const inner = l.inner_h || 25;
  const H = BOT + inner;
  const cols = l.cols || 1;
  const rows = l.rows || 1;
  const tray = new THREE.Group();
  const lid = new THREE.Group();
  const wallC = 0x1e293b;
  const postC = 0x64748b;
  const pcbC = 0x166534;
  const bossC = 0xf59e0b;

  const wallMat = new THREE.MeshLambertMaterial({ color: wallC });
  function box(parent, w, h, d, x, y, z, mat) {
    const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat || wallMat);
    m.position.set(x, y, z);
    parent.add(m);
    return m;
  }

  for (let i = 0; i < rows; i++) {
    const t = (tiltOf(l, i) * Math.PI) / 180;
    const row = new THREE.Group();
    row.position.set(0, accumY(l, i), accumZ(l, i));
    row.rotation.x = t;
    const y0 = i === 0 ? -WALL : 0;
    const yl = PITCH + (i === 0 ? WALL : 0) + (i === rows - 1 ? WALL : 0);
    const cw = cols * PITCH + 2 * WALL;
    box(row, cw, yl, BOT, cols * PITCH / 2, y0 + yl / 2, BOT / 2);
    box(row, WALL, yl, H, -WALL / 2, y0 + yl / 2, H / 2);
    box(row, WALL, yl, H, cols * PITCH + WALL / 2, y0 + yl / 2, H / 2);
    if (i === 0) box(row, cw, WALL, H, cols * PITCH / 2, -WALL / 2, H / 2);
    if (i === rows - 1) box(row, cw, WALL, H, cols * PITCH / 2, PITCH + WALL / 2, H / 2);
    tray.add(row);
  }

  const flat = (l.tilts || []).every((v) => !v);
  if (flat) {
    lid.add(lidWithHoles(l, inner));
  } else {
    for (let i = 0; i < rows; i++) {
      const t = (tiltOf(l, i) * Math.PI) / 180;
      const lidRow = new THREE.Group();
      lidRow.position.set(0, accumY(l, i), accumZ(l, i));
      lidRow.rotation.x = t;
      const y0 = i === 0 ? -WALL : 0;
      const yl = PITCH + (i === 0 ? WALL : 0) + (i === rows - 1 ? WALL : 0);
      const cw = cols * PITCH + 2 * WALL;
      box(lidRow, cw, yl, TOP, cols * PITCH / 2, y0 + yl / 2, BOT + inner + TOP / 2, new THREE.MeshLambertMaterial({ color: 0xd6dee8 }));
      lid.add(lidRow);
    }
  }

  const zCut = BOT + inner + TOP / 2;
  for (const { p, def } of placedDevices(l)) {
    const c = deviceCenter(p, def);
    if (def.place !== "bottom" && def.place !== "wall") {
      addCutoutMarkers(lid, c.x, c.y, zCut, def.cutouts);
      // PCB ghost under the lid
      if (def.pcb_mm) {
        const pcb = new THREE.Mesh(
          new THREE.BoxGeometry(def.pcb_mm[0], def.pcb_mm[1], 1.6),
          new THREE.MeshLambertMaterial({ color: pcbC })
        );
        pcb.position.set(c.x, c.y, BOT + inner - (def.boss_mm || 6) - 0.8);
        lid.add(pcb);
      }
      for (const h of def.holes || []) {
        const b = new THREE.Mesh(
          new THREE.CylinderGeometry(3.2, 3.2, def.boss_mm || 6, 12),
          new THREE.MeshLambertMaterial({ color: bossC })
        );
        b.position.set(c.x + h[0], c.y + h[1], BOT + inner - (def.boss_mm || 6) / 2);
        lid.add(b);
      }
    }
    if (def.place === "bottom" && def.pcb_mm) {
      const pcb = new THREE.Mesh(
        new THREE.BoxGeometry(def.pcb_mm[0], def.pcb_mm[1], 1.6),
        new THREE.MeshLambertMaterial({ color: pcbC })
      );
      pcb.position.set(c.x, c.y, BOT + 4);
      tray.add(pcb);
    }
  }

  // wall cutouts (YAPP left/right/front/back planes)
  for (const w of l.walls || []) {
    const def = byId()[w.id];
    if (!def) continue;
    const cuts = def.cutouts || (def.wall_cutout ? [def.wall_cutout] : []);
    const pos = (w.pos + 0.5) * PITCH;
    const z = BOT + inner / 2;
    const grp = new THREE.Group();
    if (w.side === "left") grp.position.set(-WALL / 2, pos, z);
    else if (w.side === "right") grp.position.set(cols * PITCH + WALL / 2, pos, z);
    else if (w.side === "front") grp.position.set(pos, -WALL / 2, z);
    else grp.position.set(pos, rows * PITCH + WALL / 2, z);
    const wc = def.wall_cutout || cuts[0];
    if (wc && wc.type === "hole") {
      const m = new THREE.Mesh(
        new THREE.CylinderGeometry((wc.d || 8) / 2, (wc.d || 8) / 2, WALL + 2, 20),
        new THREE.MeshBasicMaterial({ color: CUT })
      );
      m.rotation.z = Math.PI / 2;
      if (w.side === "front" || w.side === "back") m.rotation.z = 0;
      if (w.side === "front" || w.side === "back") m.rotation.x = Math.PI / 2;
      grp.add(m);
    } else if (wc && wc.type === "grill") {
      const m = new THREE.Mesh(
        new THREE.BoxGeometry(WALL + 2, wc.w || 12, wc.h || 8),
        new THREE.MeshBasicMaterial({ color: CUT })
      );
      grp.add(m);
    }
    tray.add(grp);
  }

  const pegGeom = new THREE.CylinderGeometry(PEG_D / 2, PEG_D / 2, PEG_H, 12);
  const postMat = new THREE.MeshLambertMaterial({ color: postC });
  const pegZ = BOT + inner - PEG_H / 2;
  function addPeg(x, y) {
    const p = new THREE.Mesh(pegGeom, postMat);
    p.position.set(x, y, pegZ);
    lid.add(p);
  }
  for (let r = 0; r < rows; r++) {
    if (Math.abs(tiltOf(l, r)) >= 0.05) continue;
    addPeg(-PEG_INSET, (r + 0.5) * PITCH);
    addPeg(cols * PITCH + PEG_INSET, (r + 0.5) * PITCH);
  }
  const yf = -PEG_INSET;
  const yb = rows * PITCH + PEG_INSET;
  if (cols > 1) {
    for (let c = 1; c < cols; c++) addPeg(c * PITCH, yf), addPeg(c * PITCH, yb);
  } else {
    addPeg(PITCH / 2, yf);
    addPeg(PITCH / 2, yb);
  }

  const skirtMat = new THREE.MeshLambertMaterial({ color: 0xcbd5e1 });
  const zSk = BOT + inner - SKIRT_H / 2;
  const cw = cols * PITCH + 2 * WALL + 2 * EX;
  const cd = rows * PITCH + 2 * WALL + 2 * EX;
  box(lid, cw, SKIRT, SKIRT_H, cols * PITCH / 2, -WALL - FIT - SKIRT / 2, zSk, skirtMat);
  box(lid, cw, SKIRT, SKIRT_H, cols * PITCH / 2, rows * PITCH + WALL + FIT + SKIRT / 2, zSk, skirtMat);
  box(lid, SKIRT, cd - 2 * SKIRT, SKIRT_H, -WALL - FIT - SKIRT / 2, rows * PITCH / 2, zSk, skirtMat);
  box(lid, SKIRT, cd - 2 * SKIRT, SKIRT_H, cols * PITCH + WALL + FIT + SKIRT / 2, rows * PITCH / 2, zSk, skirtMat);

  if (viewMode === "bottom") g.add(tray);
  else if (viewMode === "top") {
    lid.position.z += 10;
    g.add(lid);
  } else {
    g.add(tray);
    g.add(lid);
  }
  g.rotation.x = -Math.PI / 2;
  return g;
}

export function rebuildPreview() {
  if (!scene) return;
  if (root) {
    scene.remove(root);
    root.traverse((o) => {
      if (o.geometry) o.geometry.dispose();
    });
  }
  root = build(layout());
  scene.add(root);
  const box = new THREE.Box3().setFromObject(root);
  if (!box.isEmpty() && controls && camera) {
    const c = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z, 40);
    controls.target.copy(c);
    camera.position.set(c.x + maxDim * 1.15, c.y + maxDim * 0.95, c.z + maxDim * 1.25);
    camera.near = 0.5;
    camera.far = Math.max(4000, maxDim * 20);
    camera.updateProjectionMatrix();
    controls.update();
  }
}

function init() {
  const el = document.getElementById("view3d");
  if (!el) return;
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x02080d);
  camera = new THREE.PerspectiveCamera(40, el.clientWidth / Math.max(el.clientHeight, 1), 1, 4000);
  camera.position.set(200, 170, 240);
  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(window.devicePixelRatio || 1);
  renderer.setSize(el.clientWidth, el.clientHeight);
  el.appendChild(renderer.domElement);
  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  scene.add(new THREE.AmbientLight(0xffffff, 0.6));
  const dir = new THREE.DirectionalLight(0xffffff, 0.85);
  dir.position.set(90, 160, 70);
  scene.add(dir);
  scene.add(new THREE.GridHelper(420, 16, 0x155e75, 0x0b2a33));
  rebuildPreview();
  window.addEventListener("resize", () => {
    camera.aspect = el.clientWidth / Math.max(el.clientHeight, 1);
    camera.updateProjectionMatrix();
    renderer.setSize(el.clientWidth, el.clientHeight);
  });
  document.querySelectorAll("[data-view]").forEach((b) => {
    b.addEventListener("click", () => {
      viewMode = b.getAttribute("data-view");
      rebuildPreview();
    });
  });
  (function loop() {
    requestAnimationFrame(loop);
    controls.update();
    renderer.render(scene, camera);
  })();
}

window.rebuildPreview = rebuildPreview;
init();
