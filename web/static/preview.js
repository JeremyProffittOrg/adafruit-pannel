import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const PITCH = 25.4;
const WALL = 8;
const BOT = 3;
const TOP = 3.2;

let renderer, scene, camera, controls, root;
let viewMode = "assembly";

function getLayout() {
  return window.PANEL_LAYOUT;
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

function addBox(parent, w, h, d, x, y, z, color, rx = 0) {
  const m = new THREE.Mesh(
    new THREE.BoxGeometry(w, h, d),
    new THREE.MeshLambertMaterial({ color, transparent: true, opacity: 0.92 })
  );
  m.position.set(x, y, z);
  if (rx) m.rotation.x = rx;
  parent.add(m);
}

function build(l) {
  const g = new THREE.Group();
  if (!l) return g;
  const inner = l.inner_h || 25;
  const H = BOT + inner + 1.6;
  const cols = l.cols || 1;
  const rows = l.rows || 1;
  const tray = new THREE.Group();
  const lid = new THREE.Group();
  const wallC = 0x1e293b;
  const lidC = 0xcbd5e1;
  const postC = 0x94a3b8;

  for (let i = 0; i < rows; i++) {
    const t = (tiltOf(l, i) * Math.PI) / 180;
    const oy = accumY(l, i);
    const oz = accumZ(l, i);
    const row = new THREE.Group();
    row.position.set(0, oy, oz);
    row.rotation.x = t;
    const y0 = i === 0 ? -WALL : 0;
    const yl = PITCH + (i === 0 ? WALL : 0) + (i === rows - 1 ? WALL : 0);
    const cw = cols * PITCH + 2 * WALL;
    // floor
    addBox(row, cw, yl, BOT, cols * PITCH / 2, y0 + yl / 2, BOT / 2, wallC);
    // left / right walls
    addBox(row, WALL, yl, H, -WALL / 2, y0 + yl / 2, H / 2, wallC);
    addBox(row, WALL, yl, H, cols * PITCH + WALL / 2, y0 + yl / 2, H / 2, wallC);
    // front / back
    if (i === 0) addBox(row, cw, WALL, H, cols * PITCH / 2, -WALL / 2, H / 2, wallC);
    if (i === rows - 1) addBox(row, cw, WALL, H, cols * PITCH / 2, PITCH + WALL / 2, H / 2, wallC);
    // lid plate
    const lidRow = new THREE.Group();
    lidRow.position.copy(row.position);
    lidRow.rotation.copy(row.rotation);
    addBox(lidRow, cw, yl, TOP, cols * PITCH / 2, y0 + yl / 2, BOT + inner + TOP / 2, lidC);
    tray.add(row);
    lid.add(lidRow);
  }

  // world-Z posts in the rim
  const xs = [-WALL / 2, cols * PITCH + WALL / 2];
  const postGeom = new THREE.CylinderGeometry(3.4, 3.4, inner - 0.2, 12);
  const postMat = new THREE.MeshLambertMaterial({ color: postC });
  function postAt(x, y) {
    const p = new THREE.Mesh(postGeom, postMat);
    p.position.set(x, y, BOT + inner / 2);
    lid.add(p);
  }
  for (let r = 0; r <= rows; r++) {
    const i = r === rows ? rows - 1 : r;
    const ly = r === rows ? PITCH : 0;
    const y = accumY(l, i) + ly * Math.cos((tiltOf(l, i) * Math.PI) / 180);
    for (const x of xs) postAt(x, y);
  }

  if (viewMode === "bottom") g.add(tray);
  else if (viewMode === "top") {
    lid.position.z += 8;
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
  if (root) scene.remove(root);
  root = build(getLayout());
  scene.add(root);
}

function init() {
  const el = document.getElementById("view3d");
  if (!el) return;
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0b1220);
  camera = new THREE.PerspectiveCamera(40, el.clientWidth / el.clientHeight, 1, 4000);
  camera.position.set(180, 160, 220);
  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(el.clientWidth, el.clientHeight);
  el.appendChild(renderer.domElement);
  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  scene.add(new THREE.AmbientLight(0xffffff, 0.55));
  const dir = new THREE.DirectionalLight(0xffffff, 0.8);
  dir.position.set(80, 140, 60);
  scene.add(dir);
  const grid = new THREE.GridHelper(400, 16, 0x334155, 0x1e293b);
  scene.add(grid);
  rebuildPreview();
  window.addEventListener("resize", () => {
    camera.aspect = el.clientWidth / el.clientHeight;
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
