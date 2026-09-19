package main

import (
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
	body, err := buildZipBytes(l)
	if err != nil {
		return c.Status(500).SendString(err.Error())
	}
	c.Set("Content-Type", "application/zip")
	c.Set("Content-Disposition", "attachment; filename=panel-case.zip")
	return c.Send(body)
}

func handleDevices(c *fiber.Ctx) error {
	return c.SendFile(filepath.Join(repoRoot(), "library", "devices.json"))
}
