package main

import (
	"archive/zip"
	"bytes"
	"testing"
)

func TestBuildZipIncludesCad(t *testing.T) {
	if err := loadCatalog(".."); err != nil {
		t.Fatal(err)
	}
	body, err := buildZipBytes(Layout{
		Title: "3 sliders + 2 quad rotaries",
		Cols:  5, Rows: 4, InnerH: 25,
		EdgeStyle: "round", EdgeMM: 2, Hang: true, Overlap: true,
		Tilts: []float64{0, 0, 0, 0},
		Devices: []PlacedDev{
			{ID: "neoslider", C: 0, R: 0},
			{ID: "neoslider", C: 1, R: 0},
			{ID: "neoslider", C: 2, R: 0},
			{ID: "quad_rotary", C: 3, R: 0},
			{ID: "quad_rotary", C: 4, R: 0},
		},
	})
	if err != nil {
		t.Fatal(err)
	}
	zr, err := zip.NewReader(bytes.NewReader(body), int64(len(body)))
	if err != nil {
		t.Fatal(err)
	}
	have := map[string]bool{}
	for _, f := range zr.File {
		have[f.Name] = true
	}
	for _, n := range []string{
		"BOM.md", "cad/case.scad", "cad/devices.scad",
		"cad/generated/job-bottom.scad", "cad/generated/job-top.scad", "layout.json",
	} {
		if !have[n] {
			t.Fatalf("zip missing %s", n)
		}
	}
	scad := ""
	for _, f := range zr.File {
		if f.Name == "cad/generated/job-bottom.scad" {
			r, err := f.Open()
			if err != nil {
				t.Fatal(err)
			}
			b := new(bytes.Buffer)
			_, _ = b.ReadFrom(r)
			r.Close()
			scad = b.String()
		}
	}
	if !bytes.Contains([]byte(scad), []byte("NHANG = 2;")) {
		t.Fatalf("job scad missing NHANG = 2:\n%s", scad)
	}
	if !bytes.Contains([]byte(scad), []byte("OVERLAP = 1;")) {
		t.Fatalf("job scad missing OVERLAP = 1:\n%s", scad)
	}
	if !bytes.Contains([]byte(scad), []byte("FACE_TILT = 0.000;")) {
		t.Fatalf("job scad missing FACE_TILT = 0.000:\n%s", scad)
	}
	if have["bottom.stl"] && !have["case.3mf"] {
		t.Fatal("zip has STLs but no case.3mf")
	}
}

func TestFaceTiltBottomHangZip(t *testing.T) {
	if err := loadCatalog(".."); err != nil {
		t.Fatal(err)
	}
	body, err := buildZipBytes(Layout{
		Title: "wall 30",
		Cols:  4, Rows: 3, InnerH: 25,
		EdgeStyle: "round", EdgeMM: 2, Overlap: true,
		FaceTilt: 30,
		Tilts:    []float64{0, 0, 0},
		Hangs: []PlacedHang{
			{Side: "bottom", Pos: 0, Orient: "down"},
			{Side: "bottom", Pos: 3, Orient: "down"},
		},
	})
	if err != nil {
		t.Fatal(err)
	}
	zr, err := zip.NewReader(bytes.NewReader(body), int64(len(body)))
	if err != nil {
		t.Fatal(err)
	}
	scad := ""
	md := ""
	for _, f := range zr.File {
		r, err := f.Open()
		if err != nil {
			t.Fatal(err)
		}
		b := new(bytes.Buffer)
		_, _ = b.ReadFrom(r)
		r.Close()
		if f.Name == "cad/generated/job-bottom.scad" {
			scad = b.String()
		}
		if f.Name == "BOM.md" {
			md = b.String()
		}
	}
	if !bytes.Contains([]byte(scad), []byte("FACE_TILT = 30.000;")) {
		t.Fatalf("job scad missing FACE_TILT = 30:\n%s", scad)
	}
	if !bytes.Contains([]byte(scad), []byte(`"bottom"`)) {
		t.Fatalf("job scad missing hang side bottom:\n%s", scad)
	}
	if !bytes.Contains([]byte(md), []byte("sitting face tilt 30 deg")) {
		t.Fatalf("BOM missing face tilt: %s", md)
	}
}

func TestBomDefaultsEdge(t *testing.T) {
	if err := loadCatalog(".."); err != nil {
		t.Fatal(err)
	}
	l := Layout{Cols: 5, Rows: 4, InnerH: 25, Hang: true}
	normalizeLayout(&l)
	if l.EdgeStyle != "round" || l.EdgeMM != 2 {
		t.Fatalf("edge %s %v", l.EdgeStyle, l.EdgeMM)
	}
	md := bomMarkdown(l)
	if !bytes.Contains([]byte(md), []byte("Edge round 2.0 mm")) {
		t.Fatalf("markdown: %s", md)
	}
}

func TestPostCountSkipsTiltedFrontBack(t *testing.T) {
	l := Layout{Cols: 4, Rows: 6, Tilts: []float64{0, 0, 0, 30, 30, -30}}
	// left/right on rows 0,1,2 only (6) + front on row 0 (3) = 9; no back
	if n := postCount(l); n != 9 {
		t.Fatalf("postCount=%d want 9", n)
	}
}
