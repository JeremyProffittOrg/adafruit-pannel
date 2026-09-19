package main

import (
	"archive/zip"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

type Layout struct {
	Cols      int          `json:"cols"`
	Rows      int          `json:"rows"`
	InnerH    float64      `json:"inner_h"`
	Tilts     []float64    `json:"tilts"`
	EdgeStyle string       `json:"edge_style"`
	EdgeMM    float64      `json:"edge_mm"`
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

func scadEscape(s string) string {
	return strings.ReplaceAll(s, `"`, `\"`)
}

func writeLayout(path, part string, l Layout) error {
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
	var b strings.Builder
	fmt.Fprintf(&b, "// generated %s\n", time.Now().Format(time.RFC3339))
	if l.EdgeStyle == "" {
		l.EdgeStyle = "round"
	}
	if l.EdgeMM <= 0 {
		l.EdgeMM = 2
	}
	fmt.Fprintf(&b, "PART = \"%s\";\n", scadEscape(part))
	fmt.Fprintf(&b, "COLS = %d;\nROWS = %d;\nINNER_H = %.3f;\n", l.Cols, l.Rows, l.InnerH)
	fmt.Fprintf(&b, "EDGE_STYLE = \"%s\";\nEDGE_MM = %.3f;\n", scadEscape(l.EdgeStyle), l.EdgeMM)
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

func buildZip(l Layout, zipPath string) error {
	genDir := filepath.Join("cad", "generated")
	if err := os.MkdirAll(genDir, 0o755); err != nil {
		return err
	}
	bottomSCAD := filepath.Join(genDir, "job-bottom.scad")
	topSCAD := filepath.Join(genDir, "job-top.scad")
	if err := writeLayout(bottomSCAD, "bottom", l); err != nil {
		return err
	}
	if err := writeLayout(topSCAD, "top", l); err != nil {
		return err
	}
	bottom := filepath.Join(genDir, "bottom.stl")
	top := filepath.Join(genDir, "top.stl")
	exe := openscadPath()
	if err := renderPart(exe, bottomSCAD, bottom, "bottom"); err != nil {
		return err
	}
	if err := renderPart(exe, topSCAD, top, "top"); err != nil {
		return err
	}
	f, err := os.Create(zipPath)
	if err != nil {
		return err
	}
	defer f.Close()
	w := zip.NewWriter(f)
	for _, name := range []string{bottom, top, bottomSCAD, topSCAD} {
		b, err := os.ReadFile(name)
		if err != nil {
			w.Close()
			return err
		}
		zw, err := w.Create(filepath.Base(name))
		if err != nil {
			w.Close()
			return err
		}
		if _, err := zw.Write(b); err != nil {
			w.Close()
			return err
		}
	}
	return w.Close()
}
