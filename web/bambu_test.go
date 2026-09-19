package main

import (
	"archive/zip"
	"bytes"
	"encoding/binary"
	"math"
	"os"
	"testing"
)

func oneTriSTL(x0, y0, z0 float32) []byte {
	buf := make([]byte, 84+50)
	binary.LittleEndian.PutUint32(buf[80:84], 1)
	put := func(off int, v float32) {
		binary.LittleEndian.PutUint32(buf[off:], math.Float32bits(v))
	}
	put(84+12, x0)
	put(84+16, y0)
	put(84+20, z0)
	put(84+24, x0+1)
	put(84+28, y0)
	put(84+32, z0)
	put(84+36, x0)
	put(84+40, y0+1)
	put(84+44, z0)
	return buf
}

func TestBuildCase3MF(t *testing.T) {
	body, err := buildCase3MF(oneTriSTL(0, 0, 0), oneTriSTL(10, 0, 0))
	if err != nil {
		t.Fatal(err)
	}
	zr, err := zip.NewReader(bytes.NewReader(body), int64(len(body)))
	if err != nil {
		t.Fatal(err)
	}
	have := map[string]bool{}
	var model string
	for _, f := range zr.File {
		have[f.Name] = true
		if f.Name == "3D/3dmodel.model" {
			r, err := f.Open()
			if err != nil {
				t.Fatal(err)
			}
			b := new(bytes.Buffer)
			_, _ = b.ReadFrom(r)
			r.Close()
			model = b.String()
		}
	}
	for _, n := range []string{"[Content_Types].xml", "_rels/.rels", "3D/3dmodel.model"} {
		if !have[n] {
			t.Fatalf("3mf missing %s", n)
		}
	}
	if !bytes.Contains([]byte(model), []byte(`name="tray"`)) || !bytes.Contains([]byte(model), []byte(`name="lid"`)) {
		t.Fatalf("3mf missing object names:\n%s", model)
	}
	if !bytes.Contains([]byte(model), []byte(`objectid="1"`)) || !bytes.Contains([]byte(model), []byte(`objectid="2"`)) {
		t.Fatalf("3mf missing build items:\n%s", model)
	}
}

func TestBuildCase3MFFromKitSTLs(t *testing.T) {
	tray, err := os.ReadFile("../print-kits/sliders-quads-case/bottom.stl")
	if err != nil {
		t.Skip(err)
	}
	lid, err := os.ReadFile("../print-kits/sliders-quads-case/top.stl")
	if err != nil {
		t.Skip(err)
	}
	body, err := buildCase3MF(tray, lid)
	if err != nil {
		t.Fatal(err)
	}
	if len(body) < 1000 {
		t.Fatalf("3mf too small: %d", len(body))
	}
	zr, err := zip.NewReader(bytes.NewReader(body), int64(len(body)))
	if err != nil {
		t.Fatal(err)
	}
	ok := false
	for _, f := range zr.File {
		if f.Name == "3D/3dmodel.model" && f.UncompressedSize64 > 1000 {
			ok = true
		}
	}
	if !ok {
		t.Fatal("kit 3mf missing mesh")
	}
}

func TestBambuFileName(t *testing.T) {
	if g := bambuFileName("3 sliders + 2 quad rotaries"); g != "3-sliders-2-quad-rotaries.3mf" {
		t.Fatalf("got %q", g)
	}
}
