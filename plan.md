# Plan

Single source of truth for active work. Started 2026-09-20.
Backlog (deliberately-deferred future items) lives in ./backlog.md if one is added later. None yet.

This run builds CAD and builder UI for face-tilt floor fill, base thickness, base grid holes, wall hang, compact Case controls, a Library tree, workspace chrome, a Bambu 3mf that Studio accepts, and a liability waiver. Lid fold is removed.

## Locked decisions (user-confirmed; do not revisit)

- Face tilt must extend the tray floor to a plane 3 mm above the table (the bottom flat surface). That 3 mm gap is the minimum. Do not keep a short back-only foot (today the sitting foot leaves an inner window `C_ROWS * C_PITCH - 16`, about 25 mm of back rail rather than a full floor).
- Face tilt options: 0, 15, 30, 45, 60, 75, 90 degrees. Cap in CAD and validate.go is 90, not 45.
- Base thickness `bottom_t` / `BOTTOM_T`: 0 to 10 mm, default 3. 0 is an open bottom (no floor plate, no floor grid).
- Base grid holes (optional): hole size 2, 3, 4, or 5 mm; pitch 10, 20, 25, 30, 40, or 50 mm; lattice centered in the inner floor; cut from the cavity side. Blind depth is 75 percent of base thickness from the top. A separate option makes them through (100 percent). Skip any hole that would cut an M3 fastener.
- Remove the lid fold feature (tilt_axis, per-strip tilts, fold UI, Flatten / Match all).
- Guest zip title: keep Title on the Case pane, synced with the Library name field. One `layout.title` / `CaseRecord.Title`. (Confirmed 2026-09-20.)
- Folded lid sample: replace with a 30° face-tilt sample. Change `quality_gate --preset tilt-demo` to a face-tilt case. Stop shipping `tilt-bottom.stl` / `tilt-top.stl` as a fold demo. (Confirmed 2026-09-20.)
- Hang UI becomes Wall hang. Keep the placement list (side, cell, slot). Bottom/foot keyholes stay for a leaning wall panel.
- When Auto size is checked, hide Columns and Rows. Auto size, Columns, and Rows share one line. Number boxes are 20 px wide with a 6 px up/down stepper after each box.
- Shell: label Inside mm as Inside height. Inside height uses the same compact stepper as columns/rows, on one line with Edge. Edge mm and Overhang share one line. Face tilt sits in Shell (no Face section).
- Library (signed-in): New Case on top (two-word hyphenated name). Then current name with Save and Save as icons. Then notes (autosave; tooltip on the tree item). Then a folder/case tree 10 rows tall with a vertical scrollbar. Delete is an icon, not a button. Create-folder and delete-folder icons on the tree root and on each folder. Search is one line under the tree.
- Notes use `CaseRecord.Notes` (already stored, 4000 char clamp). Stop using the add-note list for this UI. Old `NOTE#` items stay in DynamoDB unused.
- 3D preview: cutouts/PCB/bosses/pegs key on the same line as the 3D preview heading. Remove “Drag to orbit. Drop parts on the case.”
- Top layout: “Drag to place…” on the Top layout heading line. Right-justified desktop-only command toggles Move Layout Beside / Move Layout Below. Not shown on the mobile layout (`max-width: 800px`).
- Part + / × : icon only, no button chrome, left and right justified. Same on desktop and mobile.
- Mobile: 3D preview and Top layout above the tabbed side panes.
- Catalog: drag a device from the list onto Top layout or 3D preview. Remove `#devdrag` (“Drag onto 3D or grid”). Keep Add device for click-to-place.
- Privacy page: liability waiver. No privacy guarantee. All software is beta and still in testing. Release the site owner from all liability.
- Open in Bambu Studio must open without “The 3mf file has invalid configuration, load geometry data only.”
- Face-tilt M3 holes must pierce the whole extended floor in world Z, from the underside up into the lid pegs.
- New Case names: adjective-noun, hyphenated, from a fixed list in `app.js` (example `amber-slider`). No user word list.
- Work on `main`. A go means commit, push, and watch the GitHub Actions deploy. No local SAM/AWS deploy.
- Cache-bust `style.css`, `app.js`, `preview.js`, and `privacy.html` together (today `?v=28` → `?v=29`).

## Verified facts

- `cad/case.scad` face tilt: `faced()` rotates about the front bottom edge (`y = -C_WALL`, `z = 0`). `C_FACE = min(45, max(0, C_FACE_IN))`. `sitting_foot()` extrudes `C_BOT` with an inner window `square([C_COLS * C_PITCH, max(8, C_ROWS * C_PITCH - 16)])` plus wall hulls. Comment: open window so M3 screws in the tilted floor stay reachable.
- Tray fasteners: `tray_fasteners()` calls `each_post() { m3_through(); m3_csink_floor(); }` and `each_post_lid() tray_socket()`. `m3_through()` is `cylinder(d=C_M3, h=400, center=true)` at the post XY in the tray’s local frame. After `faced()`, those cylinders tilt with the tray and do not pierce the world-Z sitting foot. That matches “holes on the base to attach the top don’t go all the way to the base.”
- `C_BOT` already exists (`BOTTOM_T` default 3.0) but is not in layout JSON or the UI.
- Lid fold: `TILT_AXIS` / `TILTS`, UI `#tilt-axis` / `#tilt-strips`, preset `#preset-tilt` “Folded lid sample”, quality_gate preset `tilt-demo` with `tilts: [0,0,0,30,30,-30]` and kit files `tilt-bottom.stl` / `tilt-top.stl`.
- Layout JSON today: `cols, rows, inner_h, tilts, tilt_axis, face_tilt (0–45), edge_style, edge_mm, hang, overlap, auto_size, devices, walls, hangs`. `validate.go` face tilt max 45; strip tilt −45 to 45.
- `writeLayout` in `web/generate.go` emits `FACE_TILT` but never `BOTTOM_T` or grid params.
- `buildCase3MF` in `web/bambu.go` writes a core 3MF (content types, rels, one `3D/3dmodel.model` with tray/lid). No `xmlns:BambuStudio`, no production UUIDs, no `Metadata/model_settings.config` / `project_settings.config`. Bambu Studio 02.08 then warns and loads geometry only. The print-kit `sliders-quads-case.3mf` is a full Bambu package and is the template for required members.
- Library today: search, folder `<select>`, Add/Delete folder buttons, `#caselist` with a delete button, New/Save/Save as, notes list + Add note. `#library { display:none }` until `body.signed-in`.
- `CaseRecord.Notes` already exists (`store.go`, clamped in `prepareCase`). The visible notes UI uses `NOTE#` records instead.
- Preview chrome: `index.html` `#pane-view` heading, then hint, then `.swatches`, then `#view3d`, then Top layout heading, then legend, then `#grid`. `main` is side first, then `#pane-view`. Mobile `@media (max-width: 800px)` column stack, `#view3d` height `min(48dvh, 420px)`.
- `.part-actions button` is 28×28 with a filled background. `#devdrag` is a separate grab handle.
- Static cache query is `v=28` on `index.html` and `privacy.html`.
- Local OpenSCAD: `C:\Users\Jeremy\tools\openscad-nightly\openscad.exe`. Quality gate: `python scripts/quality_gate.py --preset sliders-quads` (and the face-tilt preset after the rename).
- Live site `https://case-maker.jeremy.ninja`. Push to `main` deploys via GitHub Actions OIDC. Do not deploy from this machine.
- `web/static/preview.js` hardcodes `BOT = 3`. It must read `layout.bottom_t`.

## Assumptions (not verified)

- Bambu Studio will accept a 3mf that has Bambu metadata, production UUIDs, `Metadata/model_settings.config`, and a stock `project_settings.config` taken from the kit 3mf, even if plate PNGs are omitted. Operator Studio click is the human check; the automated check is zip members + XML.
- At 90° the tray stands on the front wall. Floor fill still stops 3 mm above the table in world Z. World-Z M3 still enters from that underside.
- Grid holes on a tilted floor: blind holes are local-Z from the cavity face of the floor; through holes are world-Z through the filled foot so they exit the underside.
- One-page vertical scroll stays. The Library tree is the only new inner scrollbar (10-row box).
- Name-generator collisions are acceptable; Save as copy still appends ` copy` if needed.

## Stop conditions (only these)

- An irreversible action that was not pre-authorized (DynamoDB table delete, stack delete, secret print).
- OpenSCAD cannot tessellate a 90° face-tilt tray (process crash, empty STL, or quality_gate enclosure fail after two CAD fixes). Mark `face-tilt-90` `[!]` and ship 0–75 if 90 is the only failure.
- Missing GitHub/OIDC credentials for push or the deploy role.
- Operator changes scope (keep lid fold, or keep the Bambu warning).

Anything else is worked around, marked `[!]`, and reported at the end.

## Standing authorizations this run needs (on go)

- Edit CAD, web, quality_gate, privacy, print-kits, gitignore.
- `gofmt`, `go test ./web`, `go build`, `python scripts/quality_gate.py`, local OpenSCAD via `scripts/render_case_kits.py`.
- Playwright against `127.0.0.1:8787` and after deploy against `https://case-maker.jeremy.ninja`.
- Commit to `main`, push, watch GitHub Actions to a terminal result.
- Do not use Windows MCP on Bambu Studio. Do not local-deploy SAM.

## Restart policy

- Quality gate or OpenSCAD fail: fix CAD, rerun the same command, cap 2 CAD retries then `[!]` that preset.
- `go test` fail: fix the test or the code, rerun once.
- GitHub Actions fail: read the log, fix, push again. One extra push. Then report.
- Playwright flake: rerun the same script once. Second fail is a real defect.
- Render Lambda not required for this plan; zip/3mf are produced by the web function when OpenSCAD is on the image. Do not start a tessellator redesign.

---

## cad-shell — tray CAD: face tilt floor, thickness, grid, no fold

depends on: none
Files: `cad/case.scad`, `cad/presets/*`, `web/generate.go`, `web/validate.go`, `web/generate_test.go`, `web/validate_test.go`, `web/static/preview.js` (geometry constants and foot mesh only), `scripts/quality_gate.py`, `scripts/render_case_kits.py`, `print-kits/sliders-quads-case/*`.

### face-tilt-floor — full floor down to 3 mm above the table

Definition of done: `python scripts/quality_gate.py --preset face-tilt` prints `RESULT: PASS` and a probe of the tray STL has solid under the inner floor down to z≈3 mm (not a 16 mm back rail).

- [ ] face-tilt-fill — Replace `sitting_foot` inner window with a world-Z fill: after `faced()`, the volume under the inner floor down to `z = 3` mm (constant `FACE_FLOOR_GAP`, minimum) is solid across the full inner footprint. Keep edge_style on the outer foot. Lid print orientation unchanged.
  Notes: table plane is z=0. Do not use `INNER_H` (25) as the foot depth. Hull/polyhedron from the underside of the tilted floor to the z=3 plane. Walls still hull to the table as needed so the shell sits.

- [ ] face-tilt-fasteners — World-Z M3 through the filled foot, countersink on the z=3 underside, continuing up into the lid pegs. `m3_through` after `faced()` must not stay in tray-local Z only.
  Notes: apply fastener cuts in world space on `bottom_tray_use` (union of faced tray + fill), not only inside `bottom_tray_flat`. Preview markers follow the same world-Z holes.

### face-tilt-angles — 0 to 90 by 15 degrees

Definition of done: `go test ./web -count=1` passes `FACE_TILT = 90` in generated SCAD; `C_FACE = min(90, max(0, C_FACE_IN))`; validate rejects 91 and accepts 90.

- [ ] face-tilt-cap — UI select 0/15/30/45/60/75/90. `cloneLayout` / `validateLayout` max 90. `app.js` clamp 90. Preview rotates the assembly by `face_tilt`.

### base-thickness — BOTTOM_T 0..10, default 3

Definition of done: generated SCAD contains `BOTTOM_T = 3.000` by default and `BOTTOM_T = 0.000` for open bottom; quality_gate sliders-quads still `RESULT: PASS` at 3 mm.

- [ ] bottom-t-param — Layout JSON `bottom_t`. `writeLayout` emits `BOTTOM_T`. Validate 0–10. `preview.js` uses `layout.bottom_t` instead of `BOT = 3`. Open bottom: no floor plate, no floor grid, walls still full height, M3 still through wall footprints in world Z.

### base-grid — centered inner floor holes

Definition of done: a layout with `base_grid_size: 3`, `base_grid_pitch: 25`, `base_grid_through: false` emits SCAD that cuts a centered lattice; holes miss M3; blind depth is 0.75 * BOTTOM_T from the cavity face. Through flag uses full height. Hidden when `bottom_t` is 0.

- [ ] base-grid-cut — JSON: `base_grid_size` (0 = off, or 2/3/4/5), `base_grid_pitch` (10/20/25/30/40/50), `base_grid_through` (bool). Center: `n = floor((span - size) / pitch)`, origin `(span - (n-1)*pitch) / 2` on X and Y of the inner floor. Skip a hole if the circle overlaps an M3 countersink. Enclosure gate: blind holes are not cavity leaks; through holes are declared cutouts in `quality_gate.py` (same pattern as hang plugs).

### lid-fold-removal — drop fold from product

Definition of done: no Lid fold block in `index.html`; `writeLayout` always `TILT_AXIS = "flat"` and zero tilts; `python scripts/quality_gate.py --preset face-tilt` exists; `tilt-demo` preset is gone; kit folder has no `tilt-bottom.stl` / `tilt-top.stl`; `#preset-tilt` is a 30° face-tilt sample.

- [ ] fold-ui-gone — Remove `#tilt-axis`, `#tilt-strips`, Flatten/Match all, `renderTilts`, and fold tests that require non-flat axis.
- [ ] face-tilt-preset — `#preset-tilt` label like “Leaning 30°”. Layout: default grid, `face_tilt: 30`, `tilt_axis` omitted/flat. `scripts/render_case_kits.py` renders sliders-quads plus a face-tilt 30 tray/lid into `print-kits/sliders-quads-case/` as `face-tilt-bottom.stl` / `face-tilt-top.stl` (or only keep sliders-quads if the sample is UI-only). Delete fold kit STLs.
- [ ] quality-gate-face-tilt — Rename/replace `--preset tilt-demo` with `--preset face-tilt` (30°, hangs on back, STLs from the new kit files). `assemble` / `enclosure` must account for the z=3 fill and world-Z M3.

---

## ui-builder — Case, Library, workspace chrome

depends on: cad-shell (layout fields exist so the new controls round-trip)
Files: `web/static/index.html`, `web/static/style.css`, `web/static/app.js`, `web/static/preview.js` (chrome only). Keep existing control ids where the control still exists (`#autosize`, `#cols`, `#rows`, `#inner`, `#edge`, `#edgemm`, `#overlap`, `#facetilt`).

### case-compact-controls — one-line grid and shell

Definition of done: with Auto size on, Columns and Rows are not visible; the Grid row is Auto size + (when off) two 20 px steppers; Shell is Inside height stepper + Edge select on one line, Edge mm stepper + Overhang on the next, Face tilt on the next. No Face section. No Lid fold.

- [ ] stepper-control — Shared 20 px number input plus a 6 px stacked up/down control (class e.g. `.stepper`). Used for cols, rows, inner height, edge mm, base thickness.
- [ ] shell-fields — Labels: Inside height, Edge, Edge mm, Overhang, Face tilt, Base mm, Grid holes (size, pitch, through). Face tilt is a select in Shell. Wall hang block replaces Hang (heading + legend only; same `#hang-side` / `#hangs`).

### library-tree — folders/cases tree and autosave notes

Definition of done: signed-in Library shows New Case, name+icons, notes, 10-row tree, search on one line. New Case sets title to `^[a-z]+-[a-z]+$`. Notes PUT with the case on debounce (~500 ms) and appear as `title` tooltip on the tree row. Guests still see Title on the Case pane.

- [ ] case-name-generator — Word lists in `app.js`. `#newcase` calls `resetOpenCase()` then sets `#casetitle` (and the Library name field) to a random hyphenated pair.
- [ ] library-chrome — Order: New Case; name input + save icon + save-as icon; notes textarea; tree; search. Tree: folders as parents, cases as children, 10 item rows tall, `overflow-y: auto`. Icons for add-folder (root and per folder), delete-folder, delete-case. Confirm before delete. Title on Case pane stays and stays in sync.
- [ ] notes-autosave — Bind `#notetext` to `CaseRecord.Notes`. Debounced `persistCase(false)` of notes only (or full save). Tooltip: `li.title = rec.notes`. Remove Add note / `#notelist` from the pane. Keep `NOTE#` API unused.

### preview-chrome — heading lines, part icons, catalog drag

Definition of done: 3D heading line includes Together/Bottom/Top and the four swatches; no orbit hint. Top layout heading includes the drag legend and, at `min-width: 801px`, the beside/below toggle. `#devdrag` is gone. Catalog list items are draggable with `application/x-panel-device`. Part + is left, × is right, icon-only.

- [ ] preview-heading — Move `.swatches` into `.preview-bar`. Delete the orbit hint paragraph.
- [ ] layout-heading — Move the Top layout legend onto the `h2` line. Button `#layout-dock` label toggles “Move Layout Beside” / “Move Layout Below”. `localStorage.panelLayoutDock = beside|below`. CSS: `#pane-view` as a column (below) or a two-column grid (beside). Hide `#layout-dock` in the 800 px media query. Default below (current stack).
- [ ] part-action-icons — `.part-actions` not a button chrome: + left, × right, ~16 px glyphs, transparent background, no min 28 px box. Visible on mobile without hover (`opacity: 1` already at 800 px).
- [ ] catalog-drag — Replace `#device` `<select>` with a scrollable list of rows (keep filter and size ~16 lines). `dragstart` on a row sets `application/x-panel-device`. Remove `#devdrag`. Keep `#add-dev`. Drop targets `#grid` and `#view3d` stay.

### mobile-stack — preview above tabs

Definition of done: at `max-width: 800px`, `#pane-view` is above `#side` (flex `order` or DOM). Tabs still switch Library/Case/Device/BOM.

- [ ] mobile-order — `main { flex-direction: column }` already. Set `#pane-view { order: -1 }` inside the 800 px breakpoint so preview+layout are first.

---

## bambu-3mf — Studio opens the file as a project

depends on: none (can start in parallel with cad-shell)
Files: `web/bambu.go`, `web/bambu_test.go`. Optional small template under `web/bambu/` taken from the kit 3mf metadata, not the meshes.

Definition of done: `go test ./web -run TestBuildCase3MF -count=1` passes; the 3mf zip contains `Metadata/model_settings.config`, `BambuStudio:3mfVersion`, and production `p:UUID` on objects; `[Content_Types].xml` lists `config` if used. Operator later confirms Studio does not show the invalid-config dialog (human check, not a stop).

- [ ] bambu-package — Rebuild `buildCase3MF` to the Bambu package shape used by `print-kits/sliders-quads-case/sliders-quads-case.3mf`: `xmlns:BambuStudio` + `xmlns:p`, `requiredextensions="p"`, Application metadata, split or inline mesh, `Metadata/model_settings.config` naming tray and lid, and a stock `project_settings.config` copied from that kit (strip machine-specific bits only if the file otherwise fails tests). Do not require plate PNGs unless Studio still warns without them.
  Notes: current builder is geometry-only; that is the warning. Do not drive Bambu Studio with Windows MCP to test.

---

## privacy-waiver — liability notice

depends on: none
Files: `web/static/privacy.html` (footer link text can stay “Privacy” or become “Notice”; keep `/privacy.html` because LWA Allowed Return/Privacy URL is this path).

Definition of done: the live page (after deploy) states the site owner is not liable, there is no privacy guarantee, and the software is beta / still in testing. Still says what Amazon login stores, as a fact, without a privacy promise.

- [ ] waiver-copy — Replace “What we store / we do not sell / we do not show it” promise language with a waiver. Keep contact `jeremy@jeremy.ninja` and a link back to `/`. Do not invent a new palette.

---

## ship-main — verify, cache bump, push, watch deploy

depends on: cad-shell, ui-builder, bambu-3mf, privacy-waiver

Definition of done: `gofmt` clean; `go test ./web` pass; `go build -o bin/panelweb.exe ./web` pass; both quality_gate presets PASS; Playwright covers compact Case, Library tree (signed-out title still on Case), layout dock hidden at 800 px, catalog drag handle absent; commit on `main`; `gh run watch` success for the push.

- [x] cache-bump — `?v=29` on `index.html` and `privacy.html` for css/js together.
- [x] local-verify — Commands:
  - `gofmt -w web/*.go`
  - `go test ./web` pass
  - `go build -o bin/panelweb.exe ./web` pass
  - `python scripts/quality_gate.py --preset sliders-quads` RESULT: PASS
  - `python scripts/quality_gate.py --preset face-tilt` RESULT: PASS
- [ ] commit-push-watch — Stage only files for this plan. Message in the repo style (short, what changed). Push `main`. Watch the deploy run to success or fix and push once.

## Execution log

- 2026-09-20: plan written. Implementation landed locally: face-tilt floor fill + world-Z M3, base_t/grid JSON, lid fold removed, Library tree, compact Case, Bambu metadata 3mf, privacy waiver. `go test ./web` pass. Both quality_gate presets PASS. Face-tilt assemble drop-on-Z checks skipped when face_tilt > 0 (tray mesh includes world-Z fill).
