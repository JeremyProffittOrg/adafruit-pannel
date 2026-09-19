package main

import (
	"archive/zip"
	"bytes"
	"testing"
)

func TestZipNamedFile(t *testing.T) {
	var buf bytes.Buffer
	w := zip.NewWriter(&buf)
	f, err := w.Create("case.3mf")
	if err != nil {
		t.Fatal(err)
	}
	if _, err := f.Write([]byte("3mf-bytes")); err != nil {
		t.Fatal(err)
	}
	if err := w.Close(); err != nil {
		t.Fatal(err)
	}
	got := zipNamedFile(buf.Bytes(), "case.3mf")
	if string(got) != "3mf-bytes" {
		t.Fatalf("got %q", got)
	}
	if zipNamedFile(buf.Bytes(), "missing") != nil {
		t.Fatal("expected nil")
	}
}
