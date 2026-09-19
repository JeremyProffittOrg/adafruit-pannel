package main

import (
	"context"
	"encoding/json"
	"os"
	"strings"
	"time"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/feature/dynamodb/attributevalue"
	"github.com/aws/aws-sdk-go-v2/service/dynamodb"
	"github.com/aws/aws-sdk-go-v2/service/dynamodb/types"
	"github.com/google/uuid"
)

type Store struct {
	db    *dynamodb.Client
	table string
}

type Folder struct {
	ID      string `json:"id" dynamodbav:"id"`
	Name    string `json:"name" dynamodbav:"name"`
	Created string `json:"created" dynamodbav:"created"`
}

type CaseRecord struct {
	ID        string   `json:"id" dynamodbav:"id"`
	Title     string   `json:"title" dynamodbav:"title"`
	FolderID  string   `json:"folder_id" dynamodbav:"folder_id"`
	Notes     string   `json:"notes" dynamodbav:"notes"`
	Layout    Layout   `json:"layout" dynamodbav:"layout"`
	Parts     []string `json:"parts" dynamodbav:"parts"`
	Created   string   `json:"created" dynamodbav:"created"`
	Updated   string   `json:"updated" dynamodbav:"updated"`
}

type NoteRecord struct {
	ID      string `json:"id" dynamodbav:"id"`
	CaseID  string `json:"case_id" dynamodbav:"case_id"`
	Text    string `json:"text" dynamodbav:"text"`
	Created string `json:"created" dynamodbav:"created"`
}

func newStore(ctx context.Context) (*Store, error) {
	table := os.Getenv("TABLE")
	if table == "" {
		return nil, nil
	}
	cfg, err := config.LoadDefaultConfig(ctx)
	if err != nil {
		return nil, err
	}
	return &Store{db: dynamodb.NewFromConfig(cfg), table: table}, nil
}

func nowISO() string { return time.Now().UTC().Format(time.RFC3339) }

func (s *Store) put(ctx context.Context, m map[string]any) error {
	av, err := attributevalue.MarshalMap(m)
	if err != nil {
		return err
	}
	_, err = s.db.PutItem(ctx, &dynamodb.PutItemInput{TableName: aws.String(s.table), Item: av})
	return err
}

func (s *Store) del(ctx context.Context, pk, sk string) error {
	_, err := s.db.DeleteItem(ctx, &dynamodb.DeleteItemInput{
		TableName: aws.String(s.table),
		Key: map[string]types.AttributeValue{
			"pk": &types.AttributeValueMemberS{Value: pk},
			"sk": &types.AttributeValueMemberS{Value: sk},
		},
	})
	return err
}

func (s *Store) queryPrefix(ctx context.Context, pk, skPrefix string) ([]map[string]types.AttributeValue, error) {
	var out []map[string]types.AttributeValue
	var start map[string]types.AttributeValue
	for {
		in := &dynamodb.QueryInput{
			TableName:              aws.String(s.table),
			KeyConditionExpression: aws.String("pk = :pk AND begins_with(sk, :p)"),
			ExpressionAttributeValues: map[string]types.AttributeValue{
				":pk": &types.AttributeValueMemberS{Value: pk},
				":p":  &types.AttributeValueMemberS{Value: skPrefix},
			},
			ExclusiveStartKey: start,
		}
		resp, err := s.db.Query(ctx, in)
		if err != nil {
			return nil, err
		}
		out = append(out, resp.Items...)
		if resp.LastEvaluatedKey == nil {
			break
		}
		start = resp.LastEvaluatedKey
	}
	return out, nil
}

func (s *Store) get(ctx context.Context, pk, sk string) (map[string]types.AttributeValue, error) {
	resp, err := s.db.GetItem(ctx, &dynamodb.GetItemInput{
		TableName: aws.String(s.table),
		Key: map[string]types.AttributeValue{
			"pk": &types.AttributeValueMemberS{Value: pk},
			"sk": &types.AttributeValueMemberS{Value: sk},
		},
	})
	if err != nil {
		return nil, err
	}
	if resp.Item == nil {
		return nil, nil
	}
	return resp.Item, nil
}

func (s *Store) upsertProfile(ctx context.Context, u sessionUser) error {
	return s.put(ctx, map[string]any{
		"pk":     userPK(u.ID),
		"sk":     "PROFILE",
		"id":     u.ID,
		"name":   u.Name,
		"email":  u.Email,
		"updated": nowISO(),
	})
}

func (s *Store) listFolders(ctx context.Context, uid string) ([]Folder, error) {
	items, err := s.queryPrefix(ctx, userPK(uid), "FOLDER#")
	if err != nil {
		return nil, err
	}
	out := make([]Folder, 0, len(items))
	for _, it := range items {
		var f Folder
		if err := attributevalue.UnmarshalMap(it, &f); err != nil {
			continue
		}
		out = append(out, f)
	}
	return out, nil
}

func (s *Store) putFolder(ctx context.Context, uid string, f Folder) (Folder, error) {
	if f.ID == "" {
		f.ID = uuid.NewString()
		f.Created = nowISO()
	}
	if f.Name == "" {
		f.Name = "Untitled folder"
	}
	err := s.put(ctx, map[string]any{
		"pk":      userPK(uid),
		"sk":      "FOLDER#" + f.ID,
		"id":      f.ID,
		"name":    f.Name,
		"created": f.Created,
	})
	return f, err
}

func (s *Store) deleteFolder(ctx context.Context, uid, id string) error {
	cases, err := s.listCases(ctx, uid)
	if err != nil {
		return err
	}
	for _, c := range cases {
		if c.FolderID == id {
			c.FolderID = ""
			if _, err := s.putCase(ctx, uid, c); err != nil {
				return err
			}
		}
	}
	return s.del(ctx, userPK(uid), "FOLDER#"+id)
}

func layoutParts(l Layout) []string {
	seen := map[string]bool{}
	var out []string
	add := func(id string) {
		if id == "" || id == "empty" || seen[id] {
			return
		}
		seen[id] = true
		out = append(out, id)
	}
	for _, d := range l.Devices {
		add(d.ID)
	}
	for _, w := range l.Walls {
		add(w.ID)
	}
	return out
}

func (s *Store) listCases(ctx context.Context, uid string) ([]CaseRecord, error) {
	items, err := s.queryPrefix(ctx, userPK(uid), "CASE#")
	if err != nil {
		return nil, err
	}
	out := make([]CaseRecord, 0, len(items))
	for _, it := range items {
		rec, err := unmarshalCase(it)
		if err != nil {
			continue
		}
		out = append(out, rec)
	}
	return out, nil
}

func unmarshalCase(it map[string]types.AttributeValue) (CaseRecord, error) {
	var row struct {
		ID         string   `dynamodbav:"id"`
		Title      string   `dynamodbav:"title"`
		FolderID   string   `dynamodbav:"folder_id"`
		Notes      string   `dynamodbav:"notes"`
		LayoutJSON string   `dynamodbav:"layout_json"`
		Parts      []string `dynamodbav:"parts"`
		Created    string   `dynamodbav:"created"`
		Updated    string   `dynamodbav:"updated"`
	}
	var rec CaseRecord
	if err := attributevalue.UnmarshalMap(it, &row); err != nil {
		return rec, err
	}
	rec.ID = row.ID
	rec.Title = row.Title
	rec.FolderID = row.FolderID
	rec.Notes = row.Notes
	rec.Parts = row.Parts
	rec.Created = row.Created
	rec.Updated = row.Updated
	if row.LayoutJSON != "" {
		_ = json.Unmarshal([]byte(row.LayoutJSON), &rec.Layout)
	}
	return rec, nil
}

func (s *Store) getCase(ctx context.Context, uid, id string) (CaseRecord, error) {
	var rec CaseRecord
	it, err := s.get(ctx, userPK(uid), "CASE#"+id)
	if err != nil || it == nil {
		return rec, err
	}
	return unmarshalCase(it)
}

func (s *Store) putCase(ctx context.Context, uid string, rec CaseRecord) (CaseRecord, error) {
	old, _ := s.getCase(ctx, uid, rec.ID)
	if rec.ID == "" {
		rec.ID = uuid.NewString()
		rec.Created = nowISO()
	}
	if rec.Created == "" {
		rec.Created = nowISO()
	}
	rec.Updated = nowISO()
	if rec.Title == "" {
		rec.Title = "Untitled case"
	}
	rec.Parts = layoutParts(rec.Layout)
	lj, err := json.Marshal(rec.Layout)
	if err != nil {
		return rec, err
	}
	if err := s.put(ctx, map[string]any{
		"pk":          userPK(uid),
		"sk":          "CASE#" + rec.ID,
		"id":          rec.ID,
		"title":       rec.Title,
		"folder_id":   rec.FolderID,
		"notes":       rec.Notes,
		"layout_json": string(lj),
		"parts":       rec.Parts,
		"created":     rec.Created,
		"updated":     rec.Updated,
	}); err != nil {
		return rec, err
	}
	oldSet := map[string]bool{}
	for _, p := range old.Parts {
		oldSet[p] = true
	}
	newSet := map[string]bool{}
	for _, p := range rec.Parts {
		newSet[p] = true
		if err := s.put(ctx, map[string]any{
			"pk":      userPK(uid),
			"sk":      "PART#" + p + "#CASE#" + rec.ID,
			"id":      rec.ID,
			"title":   rec.Title,
			"part":    p,
			"updated": rec.Updated,
		}); err != nil {
			return rec, err
		}
	}
	for p := range oldSet {
		if !newSet[p] {
			_ = s.del(ctx, userPK(uid), "PART#"+p+"#CASE#"+rec.ID)
		}
	}
	return rec, nil
}

func (s *Store) deleteCase(ctx context.Context, uid, id string) error {
	rec, err := s.getCase(ctx, uid, id)
	if err != nil {
		return err
	}
	notes, err := s.listNotes(ctx, uid, id)
	if err != nil {
		return err
	}
	for _, n := range notes {
		if err := s.del(ctx, userPK(uid), "NOTE#"+id+"#"+n.ID); err != nil {
			return err
		}
	}
	for _, p := range rec.Parts {
		_ = s.del(ctx, userPK(uid), "PART#"+p+"#CASE#"+id)
	}
	return s.del(ctx, userPK(uid), "CASE#"+id)
}

func (s *Store) listNotes(ctx context.Context, uid, caseID string) ([]NoteRecord, error) {
	items, err := s.queryPrefix(ctx, userPK(uid), "NOTE#"+caseID+"#")
	if err != nil {
		return nil, err
	}
	out := make([]NoteRecord, 0, len(items))
	for _, it := range items {
		var n NoteRecord
		if err := attributevalue.UnmarshalMap(it, &n); err != nil {
			continue
		}
		out = append(out, n)
	}
	return out, nil
}

func (s *Store) putNote(ctx context.Context, uid string, n NoteRecord) (NoteRecord, error) {
	if n.ID == "" {
		n.ID = uuid.NewString()
		n.Created = nowISO()
	}
	err := s.put(ctx, map[string]any{
		"pk":      userPK(uid),
		"sk":      "NOTE#" + n.CaseID + "#" + n.ID,
		"id":      n.ID,
		"case_id": n.CaseID,
		"text":    n.Text,
		"created": n.Created,
	})
	return n, err
}

func (s *Store) deleteNote(ctx context.Context, uid, caseID, noteID string) error {
	return s.del(ctx, userPK(uid), "NOTE#"+caseID+"#"+noteID)
}

func (s *Store) casesByPart(ctx context.Context, uid, part string) ([]CaseRecord, error) {
	items, err := s.queryPrefix(ctx, userPK(uid), "PART#"+part+"#CASE#")
	if err != nil {
		return nil, err
	}
	out := make([]CaseRecord, 0, len(items))
	for _, it := range items {
		var stub struct {
			ID    string `dynamodbav:"id"`
			Title string `dynamodbav:"title"`
		}
		if err := attributevalue.UnmarshalMap(it, &stub); err != nil || stub.ID == "" {
			continue
		}
		rec, err := s.getCase(ctx, uid, stub.ID)
		if err != nil || rec.ID == "" {
			continue
		}
		out = append(out, rec)
	}
	return out, nil
}

type SearchHit struct {
	Kind   string `json:"kind"`
	ID     string `json:"id"`
	CaseID string `json:"case_id,omitempty"`
	Title  string `json:"title"`
	Text   string `json:"text"`
}

func (s *Store) search(ctx context.Context, uid, q string) ([]SearchHit, error) {
	q = strings.ToLower(strings.TrimSpace(q))
	if q == "" {
		return []SearchHit{}, nil
	}
	var hits []SearchHit
	cases, err := s.listCases(ctx, uid)
	if err != nil {
		return nil, err
	}
	for _, rec := range cases {
		blob := strings.ToLower(rec.Title + " " + rec.Notes + " " + strings.Join(rec.Parts, " "))
		if strings.Contains(blob, q) {
			hits = append(hits, SearchHit{Kind: "case", ID: rec.ID, Title: rec.Title, Text: rec.Notes})
		}
	}
	notes, err := s.queryPrefix(ctx, userPK(uid), "NOTE#")
	if err != nil {
		return nil, err
	}
	for _, it := range notes {
		var n NoteRecord
		if err := attributevalue.UnmarshalMap(it, &n); err != nil {
			continue
		}
		if strings.Contains(strings.ToLower(n.Text), q) {
			hits = append(hits, SearchHit{Kind: "note", ID: n.ID, CaseID: n.CaseID, Title: "note", Text: n.Text})
		}
	}
	folders, err := s.listFolders(ctx, uid)
	if err != nil {
		return nil, err
	}
	for _, f := range folders {
		if strings.Contains(strings.ToLower(f.Name), q) {
			hits = append(hits, SearchHit{Kind: "folder", ID: f.ID, Title: f.Name})
		}
	}
	return hits, nil
}
