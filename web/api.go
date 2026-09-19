package main

import (
	"errors"
	"fmt"
	"log"
	"path/filepath"
	"strings"

	"github.com/gofiber/fiber/v2"
)

func apiFail(c *fiber.Ctx, err error) error {
	log.Printf("api %s %s: %v", c.Method(), c.Path(), err)
	return c.Status(500).JSON(fiber.Map{"error": "server error"})
}

func pathID(c *fiber.Ctx, name string) (string, error) {
	id := c.Params(name)
	if !validID(id) {
		return "", c.Status(400).JSON(fiber.Map{"error": "bad id"})
	}
	return id, nil
}

func needStore(c *fiber.Ctx) error {
	if store == nil {
		return c.Status(503).JSON(fiber.Map{"error": "database is not configured"})
	}
	return nil
}

func handleFolders(c *fiber.Ctx) error {
	if err := needStore(c); err != nil {
		return err
	}
	u, err := mustUser(c)
	if err != nil {
		return c.Status(401).JSON(fiber.Map{"error": err.Error()})
	}
	switch c.Method() {
	case fiber.MethodGet:
		list, err := store.listFolders(c.Context(), u.ID)
		if err != nil {
			return apiFail(c, err)
		}
		return c.JSON(list)
	case fiber.MethodPost:
		var f Folder
		if err := c.BodyParser(&f); err != nil {
			return c.Status(400).JSON(fiber.Map{"error": "bad json"})
		}
		f.ID = ""
		f.Name = clampString(f.Name, 80)
		if f.Name == "" {
			return c.Status(400).JSON(fiber.Map{"error": "folder needs a name"})
		}
		out, err := store.putFolder(c.Context(), u.ID, f)
		if err != nil {
			return apiFail(c, err)
		}
		return c.Status(201).JSON(out)
	default:
		return c.SendStatus(405)
	}
}

func handleFolder(c *fiber.Ctx) error {
	if err := needStore(c); err != nil {
		return err
	}
	u, err := mustUser(c)
	if err != nil {
		return c.Status(401).JSON(fiber.Map{"error": err.Error()})
	}
	id, err := pathID(c, "id")
	if err != nil {
		return err
	}
	switch c.Method() {
	case fiber.MethodPut:
		var f Folder
		if err := c.BodyParser(&f); err != nil {
			return c.Status(400).JSON(fiber.Map{"error": "bad json"})
		}
		f.ID = id
		f.Name = clampString(f.Name, 80)
		if f.Name == "" {
			return c.Status(400).JSON(fiber.Map{"error": "folder needs a name"})
		}
		out, err := store.putFolder(c.Context(), u.ID, f)
		if err != nil {
			return apiFail(c, err)
		}
		return c.JSON(out)
	case fiber.MethodDelete:
		if err := store.deleteFolder(c.Context(), u.ID, id); err != nil {
			return apiFail(c, err)
		}
		return c.SendStatus(204)
	default:
		return c.SendStatus(405)
	}
}

func handleCases(c *fiber.Ctx) error {
	if err := needStore(c); err != nil {
		return err
	}
	u, err := mustUser(c)
	if err != nil {
		return c.Status(401).JSON(fiber.Map{"error": err.Error()})
	}
	switch c.Method() {
	case fiber.MethodGet:
		list, err := store.listCases(c.Context(), u.ID)
		if err != nil {
			return apiFail(c, err)
		}
		folder := c.Query("folder")
		if folder == "" {
			return c.JSON(list)
		}
		if !validID(folder) {
			return c.Status(400).JSON(fiber.Map{"error": "bad id"})
		}
		filtered := make([]CaseRecord, 0)
		for _, rec := range list {
			if rec.FolderID == folder {
				filtered = append(filtered, rec)
			}
		}
		return c.JSON(filtered)
	case fiber.MethodPost:
		var rec CaseRecord
		if err := c.BodyParser(&rec); err != nil {
			return c.Status(400).JSON(fiber.Map{"error": "bad json"})
		}
		rec.ID = ""
		if err := prepareCase(&rec); err != nil {
			return c.Status(400).JSON(fiber.Map{"error": err.Error()})
		}
		out, err := store.putCase(c.Context(), u.ID, rec)
		if err != nil {
			return apiFail(c, err)
		}
		return c.Status(201).JSON(out)
	default:
		return c.SendStatus(405)
	}
}

func handleCase(c *fiber.Ctx) error {
	if err := needStore(c); err != nil {
		return err
	}
	u, err := mustUser(c)
	if err != nil {
		return c.Status(401).JSON(fiber.Map{"error": err.Error()})
	}
	id, err := pathID(c, "id")
	if err != nil {
		return err
	}
	switch c.Method() {
	case fiber.MethodGet:
		rec, err := store.getCase(c.Context(), u.ID, id)
		if err != nil {
			return apiFail(c, err)
		}
		if rec.ID == "" {
			return c.Status(404).JSON(fiber.Map{"error": "not found"})
		}
		return c.JSON(rec)
	case fiber.MethodPut:
		var rec CaseRecord
		if err := c.BodyParser(&rec); err != nil {
			return c.Status(400).JSON(fiber.Map{"error": "bad json"})
		}
		rec.ID = id
		if err := prepareCase(&rec); err != nil {
			return c.Status(400).JSON(fiber.Map{"error": err.Error()})
		}
		out, err := store.putCase(c.Context(), u.ID, rec)
		if err != nil {
			return apiFail(c, err)
		}
		return c.JSON(out)
	case fiber.MethodDelete:
		if err := store.deleteCase(c.Context(), u.ID, id); err != nil {
			return apiFail(c, err)
		}
		return c.SendStatus(204)
	default:
		return c.SendStatus(405)
	}
}

func handleNotes(c *fiber.Ctx) error {
	if err := needStore(c); err != nil {
		return err
	}
	u, err := mustUser(c)
	if err != nil {
		return c.Status(401).JSON(fiber.Map{"error": err.Error()})
	}
	caseID, err := pathID(c, "id")
	if err != nil {
		return err
	}
	switch c.Method() {
	case fiber.MethodGet:
		list, err := store.listNotes(c.Context(), u.ID, caseID)
		if err != nil {
			return apiFail(c, err)
		}
		return c.JSON(list)
	case fiber.MethodPost:
		var n NoteRecord
		if err := c.BodyParser(&n); err != nil {
			return c.Status(400).JSON(fiber.Map{"error": "bad json"})
		}
		n.ID = ""
		n.CaseID = caseID
		n.Text = clampString(n.Text, 4000)
		if n.Text == "" {
			return c.Status(400).JSON(fiber.Map{"error": "note is empty"})
		}
		out, err := store.putNote(c.Context(), u.ID, n)
		if err != nil {
			return apiFail(c, err)
		}
		return c.Status(201).JSON(out)
	default:
		return c.SendStatus(405)
	}
}

func handleNoteDelete(c *fiber.Ctx) error {
	if err := needStore(c); err != nil {
		return err
	}
	u, err := mustUser(c)
	if err != nil {
		return c.Status(401).JSON(fiber.Map{"error": err.Error()})
	}
	caseID, err := pathID(c, "id")
	if err != nil {
		return err
	}
	nid, err := pathID(c, "nid")
	if err != nil {
		return err
	}
	if err := store.deleteNote(c.Context(), u.ID, caseID, nid); err != nil {
		return apiFail(c, err)
	}
	return c.SendStatus(204)
}

func handleSearch(c *fiber.Ctx) error {
	if err := needStore(c); err != nil {
		return err
	}
	u, err := mustUser(c)
	if err != nil {
		return c.Status(401).JSON(fiber.Map{"error": err.Error()})
	}
	hits, err := store.search(c.Context(), u.ID, c.Query("q"))
	if err != nil {
		return apiFail(c, err)
	}
	return c.JSON(hits)
}

func handleCasesByPart(c *fiber.Ctx) error {
	if err := needStore(c); err != nil {
		return err
	}
	u, err := mustUser(c)
	if err != nil {
		return c.Status(401).JSON(fiber.Map{"error": err.Error()})
	}
	part, err := pathID(c, "part")
	if err != nil {
		return err
	}
	list, err := store.casesByPart(c.Context(), u.ID, part)
	if err != nil {
		return apiFail(c, err)
	}
	return c.JSON(list)
}

func handleBambuOpen(c *fiber.Ctx) error {
	var l Layout
	if err := c.BodyParser(&l); err != nil {
		return c.Status(400).JSON(fiber.Map{"error": err.Error()})
	}
	if err := validateLayout(&l); err != nil {
		return c.Status(400).JSON(fiber.Map{"error": err.Error()})
	}
	normalizeLayout(&l)
	bottom, top, err := renderCaseSTLs(l)
	if errors.Is(err, errNoOpenSCAD) {
		return c.Status(503).JSON(fiber.Map{
			"error": "this host cannot render STL, so it cannot build a Bambu project. Download the zip for OpenSCAD sources.",
		})
	}
	if err != nil {
		log.Printf("bambu render: %v", err)
		return c.Status(500).JSON(fiber.Map{"error": "could not render case for Bambu Studio"})
	}
	body, err := buildCase3MF(bottom, top)
	if err != nil {
		log.Printf("bambu 3mf: %v", err)
		return c.Status(500).JSON(fiber.Map{"error": "could not pack Bambu project"})
	}
	name := bambuFileName(l.Title)
	_, fileURL, err := publishBambu(c.Context(), name, body)
	if err != nil {
		log.Printf("bambu publish: %v", err)
		return c.Status(500).JSON(fiber.Map{"error": "could not host Bambu project"})
	}
	win, mac := bambuOpenURLs(fileURL)
	return c.JSON(fiber.Map{
		"url":          fileURL,
		"name":         name,
		"open_windows": win,
		"open_macos":   mac,
	})
}

func handleBambuGet(c *fiber.Ctx) error {
	id := strings.TrimSuffix(c.Params("id"), ".3mf")
	e, ok := loadCachedBambu(id)
	if !ok {
		return c.Status(404).SendString("bambu project expired")
	}
	c.Set("Content-Type", "model/3mf")
	c.Set("Content-Disposition", `attachment; filename="`+e.name+`"`)
	return c.Send(e.body)
}

func handleRenderStart(c *fiber.Ctx) error {
	var l Layout
	if err := c.BodyParser(&l); err != nil {
		return c.Status(400).JSON(fiber.Map{"error": err.Error()})
	}
	if err := validateLayout(&l); err != nil {
		return c.Status(400).JSON(fiber.Map{"error": err.Error()})
	}
	normalizeLayout(&l)
	id, err := startRenderJob(c.Context(), l)
	if err != nil {
		log.Printf("render start: %v", err)
		return c.Status(500).JSON(fiber.Map{"error": "could not start render"})
	}
	return c.Status(202).JSON(fiber.Map{"job_id": id})
}

func handleRenderStatus(c *fiber.Ctx) error {
	id, err := pathID(c, "id")
	if err != nil {
		return err
	}
	st, ok, err := getJobStatus(c.Context(), id)
	if err != nil {
		return apiFail(c, err)
	}
	if !ok {
		return c.Status(404).JSON(fiber.Map{"error": "unknown job"})
	}
	return c.JSON(st)
}

func handleRenderFile(c *fiber.Ctx) error {
	id, err := pathID(c, "id")
	if err != nil {
		return err
	}
	kind := c.Params("kind")
	v, ok := localBlobs.Load(id)
	if !ok {
		return c.Status(404).SendString("expired")
	}
	b := v.(jobBlobs)
	st, _, _ := getJobStatus(c.Context(), id)
	switch kind {
	case "zip":
		c.Set("Content-Type", "application/zip")
		c.Set("Content-Disposition", `attachment; filename="`+orName(st.ZipName, "panel-case.zip")+`"`)
		return c.Send(b.zip)
	case "3mf":
		c.Set("Content-Type", "model/3mf")
		c.Set("Content-Disposition", `attachment; filename="`+orName(st.ThreeMFName, "panel-case.3mf")+`"`)
		return c.Send(b.three)
	default:
		return c.SendStatus(404)
	}
}

func orName(s, fallback string) string {
	if s == "" {
		return fallback
	}
	return s
}

func handleGenerate(c *fiber.Ctx) error {
	var l Layout
	if err := c.BodyParser(&l); err != nil {
		return c.Status(400).SendString(err.Error())
	}
	if err := validateLayout(&l); err != nil {
		return c.Status(400).SendString(err.Error())
	}
	normalizeLayout(&l)
	body, err := buildZipBytes(l)
	if err != nil {
		log.Printf("generate: %v", err)
		return c.Status(500).SendString("could not build zip")
	}
	name := zipFileName(l.Title)
	c.Set("Content-Type", "application/zip")
	c.Set("Content-Disposition", `attachment; filename="`+name+`"`)
	return c.Send(body)
}

func handleBOM(c *fiber.Ctx) error {
	var l Layout
	if err := c.BodyParser(&l); err != nil {
		return c.Status(400).JSON(fiber.Map{"error": err.Error()})
	}
	if err := validateLayout(&l); err != nil {
		return c.Status(400).JSON(fiber.Map{"error": err.Error()})
	}
	normalizeLayout(&l)
	return c.JSON(fiber.Map{"lines": bomLines(l), "markdown": bomMarkdown(l)})
}

func handleDevices(c *fiber.Ctx) error {
	return c.SendFile(filepath.Join(repoRoot(), "library", "devices.json"))
}

func prepareCase(rec *CaseRecord) error {
	rec.Title = clampString(rec.Title, 120)
	rec.Notes = clampString(rec.Notes, 4000)
	if rec.FolderID != "" && !validID(rec.FolderID) {
		return fmt.Errorf("bad folder id")
	}
	if rec.ID != "" && !validID(rec.ID) {
		return fmt.Errorf("bad case id")
	}
	return validateLayout(&rec.Layout)
}
