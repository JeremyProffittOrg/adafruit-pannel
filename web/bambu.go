package main

import (
	"archive/zip"
	"bytes"
	"context"
	"encoding/binary"
	"fmt"
	"math"
	"net/url"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/s3"
	"github.com/google/uuid"
)

const (
	bambuGapMM      = 8.0
	bambuContentRel = `<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel" Target="/3D/3dmodel.model" Id="rel0"/></Relationships>`
	bambuContentTypes = `<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>`
)

type vec3 struct{ x, y, z float32 }

type stlMesh struct {
	verts []vec3
	tris  [][3]int
}

type bambuCached struct {
	body []byte
	name string
	at   time.Time
}

var bambuCache sync.Map

func parseBinSTL(b []byte) (stlMesh, error) {
	var out stlMesh
	if len(b) < 84 {
		return out, fmt.Errorf("stl too small")
	}
	n := binary.LittleEndian.Uint32(b[80:84])
	need := 84 + int(n)*50
	if len(b) < need {
		return out, fmt.Errorf("stl truncated")
	}
	idx := map[[3]int64]int{}
	vert := func(off int) int {
		v := vec3{
			math.Float32frombits(binary.LittleEndian.Uint32(b[off:])),
			math.Float32frombits(binary.LittleEndian.Uint32(b[off+4:])),
			math.Float32frombits(binary.LittleEndian.Uint32(b[off+8:])),
		}
		key := [3]int64{
			int64(math.Round(float64(v.x) * 1000)),
			int64(math.Round(float64(v.y) * 1000)),
			int64(math.Round(float64(v.z) * 1000)),
		}
		if i, ok := idx[key]; ok {
			return i
		}
		i := len(out.verts)
		idx[key] = i
		out.verts = append(out.verts, v)
		return i
	}
	out.tris = make([][3]int, 0, n)
	for i := 0; i < int(n); i++ {
		off := 84 + i*50 + 12
		out.tris = append(out.tris, [3]int{vert(off), vert(off + 12), vert(off + 24)})
	}
	if len(out.verts) == 0 || len(out.tris) == 0 {
		return out, fmt.Errorf("stl has no triangles")
	}
	return out, nil
}

func meshAABB(m stlMesh) (min, max vec3) {
	min, max = m.verts[0], m.verts[0]
	for _, v := range m.verts[1:] {
		if v.x < min.x {
			min.x = v.x
		}
		if v.y < min.y {
			min.y = v.y
		}
		if v.z < min.z {
			min.z = v.z
		}
		if v.x > max.x {
			max.x = v.x
		}
		if v.y > max.y {
			max.y = v.y
		}
		if v.z > max.z {
			max.z = v.z
		}
	}
	return min, max
}

func xmlName(s string) string {
	s = strings.Map(func(r rune) rune {
		if r == '<' || r == '>' || r == '&' || r == '"' {
			return -1
		}
		return r
	}, s)
	s = strings.TrimSpace(s)
	if s == "" {
		return "part"
	}
	return s
}

func writeObject(b *strings.Builder, id int, name string, m stlMesh) {
	fmt.Fprintf(b, `<object id="%d" name="%s" type="model"><mesh><vertices>`, id, xmlName(name))
	for _, v := range m.verts {
		fmt.Fprintf(b, `<vertex x="%.5f" y="%.5f" z="%.5f"/>`, v.x, v.y, v.z)
	}
	b.WriteString(`</vertices><triangles>`)
	for _, t := range m.tris {
		fmt.Fprintf(b, `<triangle v1="%d" v2="%d" v3="%d"/>`, t[0], t[1], t[2])
	}
	b.WriteString(`</triangles></mesh></object>`)
}

func buildCase3MF(traySTL, lidSTL []byte) ([]byte, error) {
	tray, err := parseBinSTL(traySTL)
	if err != nil {
		return nil, fmt.Errorf("tray stl: %w", err)
	}
	lid, err := parseBinSTL(lidSTL)
	if err != nil {
		return nil, fmt.Errorf("lid stl: %w", err)
	}
	tmin, tmax := meshAABB(tray)
	lmin, lmax := meshAABB(lid)
	_ = lmax
	trayTx, trayTy := -tmin.x, -tmin.y
	lidTx := (tmax.x - tmin.x) + float32(bambuGapMM) - lmin.x
	lidTy := -lmin.y

	var model strings.Builder
	model.Grow(len(tray.verts)*40 + len(lid.verts)*40 + 512)
	model.WriteString(`<?xml version="1.0" encoding="UTF-8"?>`)
	model.WriteString(`<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">`)
	model.WriteString(`<resources>`)
	writeObject(&model, 1, "tray", tray)
	writeObject(&model, 2, "lid", lid)
	model.WriteString(`</resources><build>`)
	fmt.Fprintf(&model, `<item objectid="1" transform="1 0 0 0 1 0 0 0 1 %.3f %.3f 0"/>`, trayTx, trayTy)
	fmt.Fprintf(&model, `<item objectid="2" transform="1 0 0 0 1 0 0 0 1 %.3f %.3f 0"/>`, lidTx, lidTy)
	model.WriteString(`</build></model>`)

	var buf bytes.Buffer
	zw := zip.NewWriter(&buf)
	add := func(name, body string) error {
		w, err := zw.Create(name)
		if err != nil {
			return err
		}
		_, err = w.Write([]byte(body))
		return err
	}
	if err := add("[Content_Types].xml", bambuContentTypes); err != nil {
		zw.Close()
		return nil, err
	}
	if err := add("_rels/.rels", bambuContentRel); err != nil {
		zw.Close()
		return nil, err
	}
	w, err := zw.Create("3D/3dmodel.model")
	if err != nil {
		zw.Close()
		return nil, err
	}
	if _, err := w.Write([]byte(model.String())); err != nil {
		zw.Close()
		return nil, err
	}
	if err := zw.Close(); err != nil {
		return nil, err
	}
	return buf.Bytes(), nil
}

func bambuFileName(title string) string {
	n := zipFileName(title)
	n = strings.TrimSuffix(n, ".zip")
	if n == "" {
		n = "panel-case"
	}
	return n + ".3mf"
}

func bambuOpenURLs(fileURL string) (windows, mac string) {
	return "bambustudio://open?file=" + url.QueryEscape(fileURL), "bambustudioopen://" + fileURL
}

func cacheBambu(id, name string, body []byte) {
	bambuCache.Store(id, bambuCached{body: body, name: name, at: time.Now()})
	n := 0
	bambuCache.Range(func(k, v any) bool {
		n++
		return true
	})
	if n <= 24 {
		return
	}
	var oldestID any
	var oldest time.Time
	bambuCache.Range(func(k, v any) bool {
		e := v.(bambuCached)
		if oldestID == nil || e.at.Before(oldest) {
			oldestID = k
			oldest = e.at
		}
		return true
	})
	if oldestID != nil {
		bambuCache.Delete(oldestID)
	}
}

func loadCachedBambu(id string) (bambuCached, bool) {
	v, ok := bambuCache.Load(id)
	if !ok {
		return bambuCached{}, false
	}
	return v.(bambuCached), true
}

func publishBambu(ctx context.Context, name string, body []byte) (id, fileURL string, err error) {
	id = uuid.NewString()
	cacheBambu(id, name, body)
	bucket := strings.TrimSpace(os.Getenv("BAMBU_S3_BUCKET"))
	prefix := strings.Trim(strings.TrimSpace(os.Getenv("BAMBU_S3_PREFIX")), "/")
	if bucket == "" {
		base := strings.TrimRight(publicBase(), "/")
		if base == "" {
			base = "http://127.0.0.1:8787"
		}
		return id, base + "/api/bambu/" + id + ".3mf", nil
	}
	if prefix == "" {
		prefix = "dl/adafruit-pannel/bambu"
	}
	key := prefix + "/" + id + ".3mf"
	cfg, err := config.LoadDefaultConfig(ctx)
	if err != nil {
		return id, "", err
	}
	cli := s3.NewFromConfig(cfg)
	ctype := "model/3mf"
	_, err = cli.PutObject(ctx, &s3.PutObjectInput{
		Bucket:             aws.String(bucket),
		Key:                aws.String(key),
		Body:               bytes.NewReader(body),
		ContentType:        aws.String(ctype),
		ContentDisposition: aws.String(`attachment; filename="` + name + `"`),
	})
	if err != nil {
		return id, "", err
	}
	region := os.Getenv("AWS_REGION")
	if region == "" {
		region = "us-east-1"
	}
	fileURL = "https://" + bucket + ".s3." + region + ".amazonaws.com/" + key
	return id, fileURL, nil
}
