let LIB = { devices: [] };
let byId = {};
let layout = {
  cols: 5,
  rows: 4,
  inner_h: 25,
  edge_style: "round",
  edge_mm: 2,
  tilts: [0, 0, 0, 0],
  devices: [],
  walls: [],
};
window.PANEL_LAYOUT = layout;

function bumpPreview() {
  window.PANEL_LAYOUT = layout;
  window.PANEL_BY_ID = byId;
  if (window.rebuildPreview) window.rebuildPreview();
}

const $ = (id) => document.getElementById(id);

function occMap() {
  const m = {};
  for (const d of layout.devices) {
    const def = byId[d.id];
    if (!def) continue;
    for (let x = 0; x < def.cells_x; x++) {
      for (let y = 0; y < def.cells_y; y++) {
        m[`${d.c + x},${d.r + y}`] = d;
      }
    }
  }
  return m;
}

function renderTilts() {
  const box = $("tilts");
  box.innerHTML = "";
  layout.tilts.length = layout.rows;
  for (let i = 0; i < layout.rows; i++) {
    if (layout.tilts[i] == null) layout.tilts[i] = 0;
    const lab = document.createElement("label");
    lab.textContent = `row ${i} `;
    const inp = document.createElement("input");
    inp.type = "number";
    inp.value = layout.tilts[i];
    inp.step = 5;
    inp.addEventListener("input", () => {
      layout.tilts[i] = Number(inp.value) || 0;
      bumpPreview();
    });
    lab.appendChild(inp);
    box.appendChild(lab);
  }
}

function renderGrid() {
  const g = $("grid");
  g.style.gridTemplateColumns = `repeat(${layout.cols}, 1fr)`;
  g.innerHTML = "";
  const occ = occMap();
  for (let r = 0; r < layout.rows; r++) {
    for (let c = 0; c < layout.cols; c++) {
      const el = document.createElement("div");
      el.className = "cell";
      const hit = occ[`${c},${r}`];
      if (hit) {
        el.classList.add(byId[hit.id]?.place === "bottom" ? "bottom" : "on");
        if (hit.c === c && hit.r === r) el.textContent = byId[hit.id]?.name || hit.id;
      } else {
        el.textContent = `${c},${r}`;
      }
      el.addEventListener("click", () => stamp(c, r));
      g.appendChild(el);
    }
  }
}

function stamp(c, r) {
  const id = $("device").value;
  const def = byId[id];
  if (!def || def.id === "empty") {
    layout.devices = layout.devices.filter((d) => {
      const dd = byId[d.id];
      if (!dd) return false;
      return !(c >= d.c && c < d.c + dd.cells_x && r >= d.r && r < d.r + dd.cells_y);
    });
    renderGrid();
    return;
  }
  if (c + def.cells_x > layout.cols || r + def.cells_y > layout.rows) {
    $("status").textContent = `${def.name} needs ${def.cells_x} x ${def.cells_y} cells`;
    return;
  }
  layout.devices = layout.devices.filter((d) => {
    const dd = byId[d.id];
    if (!dd) return false;
    const overlap =
      c < d.c + dd.cells_x && c + def.cells_x > d.c &&
      r < d.r + dd.cells_y && r + def.cells_y > d.r;
    return !overlap;
  });
  layout.devices.push({ id, c, r });
  renderGrid();
  bumpPreview();
}

function fillDevices() {
  const sel = $("device");
  const wsel = $("wall-dev");
  const q = ($("devfilter")?.value || "").toLowerCase();
  sel.innerHTML = "";
  wsel.innerHTML = "";
  for (const d of LIB.devices) {
    byId[d.id] = d;
    const label = `${d.category}: ${d.name}`;
    if (q && !label.toLowerCase().includes(q)) continue;
    const opt = document.createElement("option");
    opt.value = d.id;
    opt.textContent = label;
    sel.appendChild(opt);
    if (d.place === "wall") {
      const w = document.createElement("option");
      w.value = d.id;
      w.textContent = d.name;
      wsel.appendChild(w);
    }
  }
  sel.addEventListener("change", () => {
    const d = byId[sel.value];
    $("devinfo").textContent = d
      ? `${d.cells_x} x ${d.cells_y} cells. place ${d.place}. ${d.url || ""}`
      : "";
  });
}

function renderWalls() {
  const ul = $("walls");
  ul.innerHTML = "";
  layout.walls.forEach((w, i) => {
    const li = document.createElement("li");
    li.textContent = `${w.side} pos ${w.pos}: ${byId[w.id]?.name || w.id} `;
    const rm = document.createElement("button");
    rm.textContent = "remove";
    rm.onclick = () => {
      layout.walls.splice(i, 1);
      renderWalls();
    };
    li.appendChild(rm);
    ul.appendChild(li);
  });
}

function syncSize() {
  layout.cols = Number($("cols").value) || 1;
  layout.rows = Number($("rows").value) || 1;
  layout.inner_h = Number($("inner").value) || 25;
  layout.edge_style = $("edge")?.value || "round";
  layout.edge_mm = Number($("edgemm")?.value) || 2;
  renderTilts();
  renderGrid();
  bumpPreview();
}

$("cols").addEventListener("input", syncSize);
$("rows").addEventListener("input", syncSize);
$("inner").addEventListener("input", syncSize);
$("edge").addEventListener("change", syncSize);
$("edgemm").addEventListener("input", syncSize);
$("devfilter").addEventListener("input", fillDevices);
$("add-wall").addEventListener("click", () => {
  layout.walls.push({
    side: $("wall-side").value,
    id: $("wall-dev").value,
    pos: Number($("wall-pos").value) || 0,
  });
  renderWalls();
});
$("preset-sq").addEventListener("click", () => {
  $("cols").value = 5;
  $("rows").value = 4;
  $("inner").value = 25;
  layout = {
    cols: 5, rows: 4, inner_h: 25, edge_style: "round", edge_mm: 2, tilts: [0, 0, 0, 0], walls: [],
    devices: [
      { id: "neoslider", c: 0, r: 0 },
      { id: "neoslider", c: 1, r: 0 },
      { id: "neoslider", c: 2, r: 0 },
      { id: "quad_rotary", c: 3, r: 0 },
      { id: "quad_rotary", c: 4, r: 0 },
    ],
  };
  syncSize();
});
$("preset-tilt").addEventListener("click", () => {
  $("cols").value = 4;
  $("rows").value = 6;
  $("inner").value = 25;
  layout = {
    cols: 4, rows: 6, inner_h: 25, edge_style: "round", edge_mm: 2,
    tilts: [0, 0, 0, 30, 30, -30],
    devices: [],
    walls: [],
  };
  syncSize();
});
$("go").addEventListener("click", async () => {
  $("status").textContent = "Rendering OpenSCAD (bottom + top). This can take a minute.";
  const res = await fetch("/api/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(layout),
  });
  if (!res.ok) {
    $("status").textContent = await res.text();
    return;
  }
  const blob = await res.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "panel-case.zip";
  a.click();
  $("status").textContent = `zip ${blob.size} bytes. Print top as exported (already flipped).`;
});

fetch("/api/devices")
  .then((r) => r.json())
  .then((j) => {
    LIB = j;
    fillDevices();
    window.PANEL_BY_ID = byId;
    syncSize();
    $("preset-sq").click();
  });
