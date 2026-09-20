package main

import "testing"

func TestValidID(t *testing.T) {
	ok := []string{"a", "neoslider", "CASE-1", "x_y", "012"}
	for _, s := range ok {
		if !validID(s) {
			t.Fatalf("validID(%q) = false, want true", s)
		}
	}
	bad := []string{"", "has#hash", "a b", "NOTE#1", "x/y"}
	for _, s := range bad {
		if validID(s) {
			t.Fatalf("validID(%q) = true, want false", s)
		}
	}
}

func TestZipFileName(t *testing.T) {
	if g := zipFileName("3 sliders + 2 quad rotaries"); g != "3-sliders-2-quad-rotaries.zip" {
		t.Fatalf("got %q", g)
	}
}

func TestValidateFaceTiltAndHangBottom(t *testing.T) {
	l := Layout{
		Cols: 5, Rows: 4, InnerH: 25, FaceTilt: 30,
		Hangs: []PlacedHang{{Side: "bottom", Pos: 0, Orient: "down"}},
	}
	if err := validateLayout(&l); err != nil {
		t.Fatal(err)
	}
	l.FaceTilt = 91
	if err := validateLayout(&l); err == nil {
		t.Fatal("want face tilt error")
	}
	l.FaceTilt = 90
	if err := validateLayout(&l); err != nil {
		t.Fatal(err)
	}
	l.FaceTilt = 30
	l.Hangs[0].Side = "top"
	if err := validateLayout(&l); err == nil {
		t.Fatal("want hang side error")
	}
}

func TestValidateBottomTAndGrid(t *testing.T) {
	v := 3.0
	l := Layout{Cols: 5, Rows: 4, InnerH: 25, BottomT: &v, BaseGridSize: 3, BaseGridPitch: 25}
	if err := validateLayout(&l); err != nil {
		t.Fatal(err)
	}
	bad := 11.0
	l.BottomT = &bad
	if err := validateLayout(&l); err == nil {
		t.Fatal("want base thickness error")
	}
	v = 3
	l.BottomT = &v
	l.BaseGridSize = 6
	if err := validateLayout(&l); err == nil {
		t.Fatal("want grid size error")
	}
}

func TestScrewLabel(t *testing.T) {
	if screwLabel(2.1) != "M2x6 screw into PCB" {
		t.Fatalf("2.1: %s", screwLabel(2.1))
	}
	if screwLabel(2.5) != "M2.5x6 screw into PCB" {
		t.Fatalf("2.5: %s", screwLabel(2.5))
	}
	if screwLabel(3.2) != "M3x6 screw into PCB" {
		t.Fatalf("3.2: %s", screwLabel(3.2))
	}
}
