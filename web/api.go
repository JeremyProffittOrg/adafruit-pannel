package main

import (
	"fmt"
	"path/filepath"

	"github.com/gofiber/fiber/v2"
)

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
			return c.Status(500).JSON(fiber.Map{"error": err.Error()})
		}
		return c.JSON(list)
	case fiber.MethodPost:
		var f Folder
		if err := c.BodyParser(&f); err != nil {
			return c.Status(400).JSON(fiber.Map{"error": "bad json"})
		}
		f.Name = clampString(f.Name, 80)
		if f.Name == "" {
			return c.Status(400).JSON(fiber.Map{"error": "folder needs a name"})
		}
		out, err := store.putFolder(c.Context(), u.ID, f)
		if err != nil {
			return c.Status(500).JSON(fiber.Map{"error": err.Error()})
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
	id := c.Params("id")
	switch c.Method() {
	case fiber.MethodPut:
		var f Folder
		if err := c.BodyParser(&f); err != nil {
			return c.Status(400).JSON(fiber.Map{"error": "bad json"})
		}
		f.ID = id
		if !validID(id) {
			return c.Status(400).JSON(fiber.Map{"error": "bad id"})
		}
		f.Name = clampString(f.Name, 80)
		if f.Name == "" {
			return c.Status(400).JSON(fiber.Map{"error": "folder needs a name"})
		}
		out, err := store.putFolder(c.Context(), u.ID, f)
		if err != nil {
			return c.Status(500).JSON(fiber.Map{"error": err.Error()})
		}
		return c.JSON(out)
	case fiber.MethodDelete:
		if err := store.deleteFolder(c.Context(), u.ID, id); err != nil {
			return c.Status(500).JSON(fiber.Map{"error": err.Error()})
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
			return c.Status(500).JSON(fiber.Map{"error": err.Error()})
		}
		folder := c.Query("folder")
		if folder == "" {
			return c.JSON(list)
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
		if err := prepareCase(&rec); err != nil {
			return c.Status(400).JSON(fiber.Map{"error": err.Error()})
		}
		out, err := store.putCase(c.Context(), u.ID, rec)
		if err != nil {
			return c.Status(500).JSON(fiber.Map{"error": err.Error()})
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
	id := c.Params("id")
	switch c.Method() {
	case fiber.MethodGet:
		rec, err := store.getCase(c.Context(), u.ID, id)
		if err != nil {
			return c.Status(500).JSON(fiber.Map{"error": err.Error()})
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
		if !validID(id) {
			return c.Status(400).JSON(fiber.Map{"error": "bad id"})
		}
		if err := prepareCase(&rec); err != nil {
			return c.Status(400).JSON(fiber.Map{"error": err.Error()})
		}
		out, err := store.putCase(c.Context(), u.ID, rec)
		if err != nil {
			return c.Status(500).JSON(fiber.Map{"error": err.Error()})
		}
		return c.JSON(out)
	case fiber.MethodDelete:
		if err := store.deleteCase(c.Context(), u.ID, id); err != nil {
			return c.Status(500).JSON(fiber.Map{"error": err.Error()})
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
	caseID := c.Params("id")
	switch c.Method() {
	case fiber.MethodGet:
		list, err := store.listNotes(c.Context(), u.ID, caseID)
		if err != nil {
			return c.Status(500).JSON(fiber.Map{"error": err.Error()})
		}
		return c.JSON(list)
	case fiber.MethodPost:
		var n NoteRecord
		if err := c.BodyParser(&n); err != nil {
			return c.Status(400).JSON(fiber.Map{"error": "bad json"})
		}
		n.CaseID = caseID
		n.Text = clampString(n.Text, 4000)
		if n.Text == "" {
			return c.Status(400).JSON(fiber.Map{"error": "note is empty"})
		}
		if !validID(caseID) {
			return c.Status(400).JSON(fiber.Map{"error": "bad id"})
		}
		out, err := store.putNote(c.Context(), u.ID, n)
		if err != nil {
			return c.Status(500).JSON(fiber.Map{"error": err.Error()})
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
	if err := store.deleteNote(c.Context(), u.ID, c.Params("id"), c.Params("nid")); err != nil {
		return c.Status(500).JSON(fiber.Map{"error": err.Error()})
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
		return c.Status(500).JSON(fiber.Map{"error": err.Error()})
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
	list, err := store.casesByPart(c.Context(), u.ID, c.Params("part"))
	if err != nil {
		return c.Status(500).JSON(fiber.Map{"error": err.Error()})
	}
	return c.JSON(list)
}

func handleGenerate(c *fiber.Ctx) error {
	var l Layout
	if err := c.BodyParser(&l); err != nil {
		return c.Status(400).SendString(err.Error())
	}
	if err := validateLayout(&l); err != nil {
		return c.Status(400).SendString(err.Error())
	}
	body, err := buildZipBytes(l)
	if err != nil {
		return c.Status(500).SendString(err.Error())
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
