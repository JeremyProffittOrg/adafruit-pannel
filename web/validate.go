package main

import (
	"fmt"
	"regexp"
	"strings"
	"unicode/utf8"
)

var idRe = regexp.MustCompile(`^[a-zA-Z0-9_-]{1,80}$`)

func clampString(s string, n int) string {
	s = strings.TrimSpace(s)
	if utf8.RuneCountInString(s) <= n {
		return s
	}
	r := []rune(s)
	return string(r[:n])
}

func validID(s string) bool {
	return idRe.MatchString(s)
}

func validateLayout(l *Layout) error {
	if l.Cols < 1 || l.Cols > 16 || l.Rows < 1 || l.Rows > 16 {
		return fmt.Errorf("grid must be 1 to 16 cells on each side")
	}
	if l.InnerH < 8 || l.InnerH > 80 {
		return fmt.Errorf("inside height must be 8 to 80 mm")
	}
	if l.EdgeMM < 0 || l.EdgeMM > 8 {
		return fmt.Errorf("edge mm must be 0 to 8")
	}
	switch l.EdgeStyle {
	case "", "round", "chamfer", "square":
	default:
		return fmt.Errorf("edge must be round, chamfer, or square")
	}
	if len(l.Devices) > 64 || len(l.Walls) > 32 {
		return fmt.Errorf("too many parts on this case")
	}
	if len(l.Tilts) < l.Rows {
		for len(l.Tilts) < l.Rows {
			l.Tilts = append(l.Tilts, 0)
		}
	}
	type span struct {
		id             string
		c0, r0, c1, r1 int
	}
	var used []span
	for _, d := range l.Devices {
		if !validID(d.ID) {
			return fmt.Errorf("bad device id")
		}
		def, ok := catalogByID[d.ID]
		if !ok || d.ID == "empty" {
			return fmt.Errorf("unknown device %s", d.ID)
		}
		dx, dy := def.CellsX, def.CellsY
		if dx < 1 {
			dx = 1
		}
		if dy < 1 {
			dy = 1
		}
		if d.C < 0 || d.R < 0 || d.C+dx > l.Cols || d.R+dy > l.Rows {
			return fmt.Errorf("%s does not fit at column %d row %d", def.Name, d.C, d.R)
		}
		s := span{d.ID, d.C, d.R, d.C + dx, d.R + dy}
		for _, o := range used {
			if s.c0 < o.c1 && o.c0 < s.c1 && s.r0 < o.r1 && o.r0 < s.r1 {
				return fmt.Errorf("%s overlaps another part", def.Name)
			}
		}
		used = append(used, s)
	}
	for _, w := range l.Walls {
		if !validID(w.ID) {
			return fmt.Errorf("bad wall device id")
		}
		if _, ok := catalogByID[w.ID]; !ok {
			return fmt.Errorf("unknown wall part %s", w.ID)
		}
		switch w.Side {
		case "left", "right", "front", "back":
		default:
			return fmt.Errorf("wall side must be left, right, front, or back")
		}
		if w.Pos < 0 || w.Pos > 32 {
			return fmt.Errorf("wall position out of range")
		}
	}
	if len(l.Hangs) > 16 {
		return fmt.Errorf("too many hang holes")
	}
	for _, h := range l.Hangs {
		switch h.Side {
		case "left", "right", "front", "back":
		default:
			return fmt.Errorf("hang side must be left, right, front, or back")
		}
		switch h.Orient {
		case "", "down", "up", "left", "right":
		default:
			return fmt.Errorf("hang orientation must be down, up, left, or right")
		}
		if h.Pos < 0 || h.Pos > 32 {
			return fmt.Errorf("hang position out of range")
		}
	}
	return nil
}

func zipFileName(title string) string {
	title = clampString(title, 60)
	var b strings.Builder
	for _, r := range strings.ToLower(title) {
		if (r >= 'a' && r <= 'z') || (r >= '0' && r <= '9') || r == '-' {
			b.WriteRune(r)
		} else if r == ' ' || r == '_' {
			b.WriteByte('-')
		}
	}
	s := strings.Trim(b.String(), "-")
	for strings.Contains(s, "--") {
		s = strings.ReplaceAll(s, "--", "-")
	}
	if s == "" {
		s = "panel-case"
	}
	return s + ".zip"
}
