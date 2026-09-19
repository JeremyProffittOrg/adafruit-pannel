package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"sync"
)

var genMu sync.Mutex

func repoRoot() string {
	wd, _ := os.Getwd()
	if _, err := os.Stat(filepath.Join(wd, "cad", "case.scad")); err == nil {
		return wd
	}
	if _, err := os.Stat(filepath.Join(wd, "..", "cad", "case.scad")); err == nil {
		return filepath.Join(wd, "..")
	}
	return wd
}

func main() {
	root := repoRoot()
	if err := os.Chdir(root); err != nil {
		log.Fatal(err)
	}
	mux := http.NewServeMux()
	mux.Handle("/", http.FileServer(http.Dir(filepath.Join(root, "web", "static"))))
	mux.HandleFunc("/api/devices", func(w http.ResponseWriter, r *http.Request) {
		http.ServeFile(w, r, filepath.Join(root, "library", "devices.json"))
	})
	mux.HandleFunc("/api/generate", handleGenerate)
	addr := ":8787"
	if p := os.Getenv("PORT"); p != "" {
		addr = ":" + p
	}
	fmt.Printf("panel web  http://127.0.0.1%s\n", addr)
	log.Fatal(http.ListenAndServe(addr, mux))
}

func handleGenerate(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "POST only", http.StatusMethodNotAllowed)
		return
	}
	body, err := io.ReadAll(io.LimitReader(r.Body, 1<<20))
	if err != nil {
		http.Error(w, err.Error(), 400)
		return
	}
	var l Layout
	if err := json.Unmarshal(body, &l); err != nil {
		http.Error(w, err.Error(), 400)
		return
	}
	genMu.Lock()
	defer genMu.Unlock()
	zipPath := filepath.Join("cad", "generated", "panel.zip")
	if err := buildZip(l, zipPath); err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	w.Header().Set("Content-Type", "application/zip")
	w.Header().Set("Content-Disposition", "attachment; filename=panel-case.zip")
	http.ServeFile(w, r, zipPath)
}
