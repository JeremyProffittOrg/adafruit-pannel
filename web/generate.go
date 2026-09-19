package main

import (
	"archive/zip"
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
	"time"
)

type CatalogDevice struct {
	ID       string      `json:"id"`
	Name     string      `json:"name"`
	Brand    string      `json:"brand"`
	Category string      `json:"category"`
	URL      string      `json:"url"`
	Place    string      `json:"place"`
	Holes    [][]float64 `json:"holes"`
	HoleD    float64     `json:"hole_d"`
	CellsX   int         `json:"cells_x"`
	CellsY   int         `json:"cells_y"`
}

type catalogFile struct {
	Devices []CatalogDevice `json:"devices"`
}

var catalogByID = map[string]CatalogDevice{}

func loadCatalog(root string) error {
	b, err := os.ReadFile(filepath.Join(root, "library", "devices.json"))
	if err != nil {
		return err
	}
	var cf catalogFile
	if err := json.Unmarshal(b, &cf); err != nil {
		return err
	}
	m := make(map[string]CatalogDevice, len(cf.Devices))
	for _, d := range cf.Devices {
		m[d.ID] = d
	}
	catalogByID = m
	return nil
}

type Layout struct {
	Title     string       `json:"title,omitempty"`
	Cols      int          `json:"cols"`
	Rows      int          `json:"rows"`
	InnerH    float64      `json:"inner_h"`
	Tilts     []float64    `json:"tilts"`
	EdgeStyle string       `json:"edge_style"`
	EdgeMM    float64      `json:"edge_mm"`
	Hang      bool         `json:"hang"`
	Overlap   bool         `json:"overlap"`
	Hangs     []PlacedHang `json:"hangs"`
	Devices   []PlacedDev  `json:"devices"`
	Walls     []PlacedWall `json:"walls"`
}

type PlacedDev struct {
	ID string `json:"id"`
	C  int    `json:"c"`
	R  int    `json:"r"`
}

type PlacedWall struct {
	Side string `json:"side"`
	ID   string `json:"id"`
	Pos  int    `json:"pos"`
}

type PlacedHang struct {
	Side   string `json:"side"`
	Pos    int    `json:"pos"`
	Orient string `json:"orient"`
}

func effectiveHangs(l Layout) []PlacedHang {
	if len(l.Hangs) > 0 {
		return l.Hangs
	}
	if !l.Hang {
		return nil
	}
	if l.Cols > 1 {
		return []PlacedHang{
			{Side: "back", Pos: 0, Orient: "down"},
			{Side: "back", Pos: l.Cols - 1, Orient: "down"},
		}
	}
	return []PlacedHang{{Side: "back", Pos: 0, Orient: "down"}}
}

func scadEscape(s string) string {
	return strings.ReplaceAll(s, `"`, `\"`)
}

func normalizeLayout(l *Layout) {
	if l.Cols < 1 {
		l.Cols = 1
	}
	if l.Rows < 1 {
		l.Rows = 1
	}
	if l.InnerH < 8 {
		l.InnerH = 8
	}
	if len(l.Tilts) < l.Rows {
		for len(l.Tilts) < l.Rows {
			l.Tilts = append(l.Tilts, 0)
		}
	}
	if l.EdgeStyle == "" {
		l.EdgeStyle = "round"
		if l.EdgeMM == 0 {
			l.EdgeMM = 2
		}
	}
	if l.EdgeMM < 0 {
		l.EdgeMM = 2
	}
}

func writeLayout(path, part string, l Layout) error {
	normalizeLayout(&l)
	var b strings.Builder
	fmt.Fprintf(&b, "// generated %s\n", time.Now().Format(time.RFC3339))
	fmt.Fprintf(&b, "PART = \"%s\";\n", scadEscape(part))
	fmt.Fprintf(&b, "COLS = %d;\nROWS = %d;\nINNER_H = %.3f;\n", l.Cols, l.Rows, l.InnerH)
	fmt.Fprintf(&b, "EDGE_STYLE = \"%s\";\nEDGE_MM = %.3f;\n", scadEscape(l.EdgeStyle), l.EdgeMM)
	hangs := effectiveHangs(l)
	fmt.Fprintf(&b, "HANG = %d;\n", map[bool]int{true: 1, false: 0}[len(hangs) > 0])
	fmt.Fprintf(&b, "OVERLAP = %d;\n", map[bool]int{true: 1, false: 0}[l.Overlap])
	fmt.Fprintf(&b, "NHANG = %d;\n", len(hangs))
	if len(hangs) > 0 {
		b.WriteString("HANG_SIDE = [")
		for i, h := range hangs {
			if i > 0 {
				b.WriteString(", ")
			}
			fmt.Fprintf(&b, `"%s"`, scadEscape(h.Side))
		}
		b.WriteString("];\nHANG_POS = [")
		for i, h := range hangs {
			if i > 0 {
				b.WriteString(", ")
			}
			fmt.Fprintf(&b, "%d", h.Pos)
		}
		b.WriteString("];\nHANG_ORIENT = [")
		for i, h := range hangs {
			if i > 0 {
				b.WriteString(", ")
			}
			o := h.Orient
			if o == "" {
				o = "down"
			}
			fmt.Fprintf(&b, `"%s"`, scadEscape(o))
		}
		b.WriteString("];\n")
	}
	b.WriteString("TILTS = [")
	for i, t := range l.Tilts[:l.Rows] {
		if i > 0 {
			b.WriteString(", ")
		}
		fmt.Fprintf(&b, "%.3f", t)
	}
	b.WriteString("];\n")
	fmt.Fprintf(&b, "NDEV = %d;\n", len(l.Devices))
	if len(l.Devices) > 0 {
		b.WriteString("DEV_ID = [")
		for i, d := range l.Devices {
			if i > 0 {
				b.WriteString(", ")
			}
			fmt.Fprintf(&b, `"%s"`, scadEscape(d.ID))
		}
		b.WriteString("];\nDEV_C = [")
		for i, d := range l.Devices {
			if i > 0 {
				b.WriteString(", ")
			}
			fmt.Fprintf(&b, "%d", d.C)
		}
		b.WriteString("];\nDEV_R = [")
		for i, d := range l.Devices {
			if i > 0 {
				b.WriteString(", ")
			}
			fmt.Fprintf(&b, "%d", d.R)
		}
		b.WriteString("];\n")
	}
	fmt.Fprintf(&b, "NWALL = %d;\n", len(l.Walls))
	if len(l.Walls) > 0 {
		b.WriteString("WALL_SIDE = [")
		for i, w := range l.Walls {
			if i > 0 {
				b.WriteString(", ")
			}
			fmt.Fprintf(&b, `"%s"`, scadEscape(w.Side))
		}
		b.WriteString("];\nWALL_ID = [")
		for i, w := range l.Walls {
			if i > 0 {
				b.WriteString(", ")
			}
			fmt.Fprintf(&b, `"%s"`, scadEscape(w.ID))
		}
		b.WriteString("];\nWALL_POS = [")
		for i, w := range l.Walls {
			if i > 0 {
				b.WriteString(", ")
			}
			fmt.Fprintf(&b, "%d", w.Pos)
		}
		b.WriteString("];\n")
	}
	b.WriteString("include <../case.scad>\n")
	return os.WriteFile(path, []byte(b.String()), 0o644)
}

func openscadPath() string {
	if p := os.Getenv("OPENSCAD"); p != "" {
		return p
	}
	candidates := []string{
		`C:\Users\Jeremy\tools\openscad-nightly\openscad.exe`,
		`C:\Program Files\OpenSCAD\openscad.exe`,
		"openscad",
	}
	for _, p := range candidates {
		if _, err := os.Stat(p); err == nil {
			return p
		}
	}
	return "openscad"
}

func renderPart(exe, layout, out, part string) error {
	cmd := exec.Command(exe,
		"-o", out,
		"--export-format=binstl",
		layout,
	)
	outb, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("openscad %s: %w\n%s", part, err, outb)
	}
	return nil
}

func rowFlat(l Layout, r int) bool {
	if r < 0 || r >= l.Rows {
		return false
	}
	t := 0.0
	if r < len(l.Tilts) {
		t = l.Tilts[r]
	}
	return t < 0.05 && t > -0.05
}

func lidBomItem(l Layout) string {
	if l.Overlap {
		return "Lid (printed, face on bed, skirt overlaps tray)"
	}
	return "Lid (printed, face on bed, flush — no overlap)"
}

func hangCount(l Layout) int {
	return len(effectiveHangs(l))
}

func postCount(l Layout) int {
	n := 0
	for r := 0; r < l.Rows; r++ {
		if rowFlat(l, r) {
			n += 2
		}
	}
	end := 0
	if rowFlat(l, 0) {
		end++
	}
	if l.Rows > 0 && rowFlat(l, l.Rows-1) {
		end++
	}
	if end > 0 {
		if l.Cols > 1 {
			n += end * (l.Cols - 1)
		} else {
			n += end
		}
	}
	return n
}

func screwLabel(d float64) string {
	if d <= 0 {
		return ""
	}
	switch {
	case d < 2.35:
		return "M2x6 screw into PCB"
	case d < 2.75:
		return "M2.5x6 screw into PCB"
	default:
		return "M3x6 screw into PCB"
	}
}

func pcbScrewLines(l Layout) []bomLine {
	qty := map[string]int{}
	for _, d := range l.Devices {
		def, ok := catalogByID[d.ID]
		if !ok || len(def.Holes) == 0 {
			continue
		}
		lab := screwLabel(def.HoleD)
		if lab == "" {
			continue
		}
		qty[lab] += len(def.Holes)
	}
	keys := make([]string, 0, len(qty))
	for k := range qty {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	out := make([]bomLine, 0, len(keys))
	for _, k := range keys {
		out = append(out, bomLine{qty[k], k, "hardware", ""})
	}
	return out
}

type bomLine struct {
	Qty  int
	Item string
	Kind string
	URL  string
}

func bomLines(l Layout) []bomLine {
	out := []bomLine{
		{1, "Bottom tray (printed)", "print", ""},
		{1, lidBomItem(l), "print", ""},
	}
	if n := postCount(l); n > 0 {
		out = append(out, bomLine{n, "M3 screw from below (tray into lid peg)", "hardware", ""})
	}
	if n := hangCount(l); n > 0 {
		out = append(out, bomLine{n, "Wall screw for keyhole (#8 / M4)", "hardware", ""})
	}
	out = append(out, pcbScrewLines(l)...)
	qty := map[string]int{}
	order := []string{}
	add := func(id string) {
		if id == "" || id == "empty" {
			return
		}
		if _, ok := qty[id]; !ok {
			order = append(order, id)
		}
		qty[id]++
	}
	for _, d := range l.Devices {
		add(d.ID)
	}
	for _, w := range l.Walls {
		add(w.ID)
	}
	sort.Strings(order)
	for _, id := range order {
		name, url, brand := id, "", ""
		if def, ok := catalogByID[id]; ok {
			name = def.Name
			url = def.URL
			brand = def.Brand
		}
		item := name
		if brand != "" && !strings.Contains(strings.ToLower(name), strings.ToLower(brand)) {
			item = brand + " " + name
		}
		out = append(out, bomLine{qty[id], item, "part", url})
	}
	return out
}

func bomCSV(l Layout) string {
	var b strings.Builder
	b.WriteString("qty,item,kind,url\n")
	for _, row := range bomLines(l) {
		fmt.Fprintf(&b, "%d,\"%s\",%s,%s\n", row.Qty, strings.ReplaceAll(row.Item, `"`, `""`), row.Kind, row.URL)
	}
	return b.String()
}

func bomMarkdown(l Layout) string {
	var b strings.Builder
	b.WriteString("# Bill of materials\n\n")
	fmt.Fprintf(&b, "Grid %d x %d. Inside height %.1f mm. Edge %s %.1f mm.\n\n", l.Cols, l.Rows, l.InnerH, l.EdgeStyle, l.EdgeMM)
	b.WriteString("| Qty | Item | Kind | Link |\n| ---: | --- | --- | --- |\n")
	for _, row := range bomLines(l) {
		link := ""
		if row.URL != "" {
			link = "[" + row.URL + "](" + row.URL + ")"
		}
		fmt.Fprintf(&b, "| %d | %s | %s | %s |\n", row.Qty, row.Item, row.Kind, link)
	}
	b.WriteString("\nPrint the lid as exported (visible face on the bed).\n")
	b.WriteString("If this zip has no STL files, install OpenSCAD and run from the zip root:\n\n")
	b.WriteString("    openscad -o bottom.stl cad/generated/job-bottom.scad\n")
	b.WriteString("    openscad -o top.stl cad/generated/job-top.scad\n")
	return b.String()
}

func layoutJSON(l Layout) ([]byte, error) {
	normalizeLayout(&l)
	return json.MarshalIndent(l, "", "  ")
}

func buildZip(l Layout, zipPath string) error {
	body, err := buildZipBytes(l)
	if err != nil {
		return err
	}
	return os.WriteFile(zipPath, body, 0o644)
}

func buildZipBytes(l Layout) ([]byte, error) {
	root := repoRoot()
	tmp, err := os.MkdirTemp("", "panel-zip-*")
	if err != nil {
		return nil, err
	}
	defer os.RemoveAll(tmp)
	cad := filepath.Join(tmp, "cad")
	genDir := filepath.Join(cad, "generated")
	if err := os.MkdirAll(genDir, 0o755); err != nil {
		return nil, err
	}
	for _, name := range []string{"case.scad", "devices.scad"} {
		src := filepath.Join(root, "cad", name)
		b, err := os.ReadFile(src)
		if err != nil {
			return nil, err
		}
		if err := os.WriteFile(filepath.Join(cad, name), b, 0o644); err != nil {
			return nil, err
		}
	}
	bottomSCAD := filepath.Join(genDir, "job-bottom.scad")
	topSCAD := filepath.Join(genDir, "job-top.scad")
	if err := writeLayout(bottomSCAD, "bottom", l); err != nil {
		return nil, err
	}
	if err := writeLayout(topSCAD, "top", l); err != nil {
		return nil, err
	}
	files := map[string][]byte{}
	addFile := func(name, path string) error {
		b, err := os.ReadFile(path)
		if err != nil {
			return err
		}
		files[name] = b
		return nil
	}
	if err := addFile("cad/generated/job-bottom.scad", bottomSCAD); err != nil {
		return nil, err
	}
	if err := addFile("cad/generated/job-top.scad", topSCAD); err != nil {
		return nil, err
	}
	if err := addFile("cad/case.scad", filepath.Join(cad, "case.scad")); err != nil {
		return nil, err
	}
	if err := addFile("cad/devices.scad", filepath.Join(cad, "devices.scad")); err != nil {
		return nil, err
	}
	exe := openscadPath()
	if p, err := exec.LookPath(exe); err == nil {
		exe = p
	}
	if _, err := os.Stat(exe); err == nil {
		bottom := filepath.Join(genDir, "bottom.stl")
		top := filepath.Join(genDir, "top.stl")
		if err := renderPart(exe, bottomSCAD, bottom, "bottom"); err != nil {
			return nil, err
		}
		if err := renderPart(exe, topSCAD, top, "top"); err != nil {
			return nil, err
		}
		if err := addFile("bottom.stl", bottom); err != nil {
			return nil, err
		}
		if err := addFile("top.stl", top); err != nil {
			return nil, err
		}
	}
	lj, err := layoutJSON(l)
	if err != nil {
		return nil, err
	}
	files["layout.json"] = lj
	files["BOM.csv"] = []byte(bomCSV(l))
	files["BOM.md"] = []byte(bomMarkdown(l))

	var buf bytes.Buffer
	w := zip.NewWriter(&buf)
	for _, name := range []string{
		"BOM.md", "BOM.csv", "layout.json",
		"cad/case.scad", "cad/devices.scad",
		"cad/generated/job-bottom.scad", "cad/generated/job-top.scad",
		"bottom.stl", "top.stl",
	} {
		b, ok := files[name]
		if !ok {
			continue
		}
		zw, err := w.Create(name)
		if err != nil {
			w.Close()
			return nil, err
		}
		if _, err := zw.Write(b); err != nil {
			w.Close()
			return nil, err
		}
	}
	if err := w.Close(); err != nil {
		return nil, err
	}
	return buf.Bytes(), nil
}
