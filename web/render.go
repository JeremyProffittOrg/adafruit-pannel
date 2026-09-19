package main

import (
	"archive/zip"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/lambda"
	lambdatypes "github.com/aws/aws-sdk-go-v2/service/lambda/types"
	"github.com/aws/aws-sdk-go-v2/service/s3"
	"github.com/google/uuid"
)

type jobBlobs struct {
	zip   []byte
	three []byte
}

var localBlobs sync.Map

const jobsPrefixDefault = "dl/adafruit-pannel/bambu/jobs"

type renderJob struct {
	JobID  string `json:"job_id"`
	Layout Layout `json:"layout"`
}

type jobStatus struct {
	State       string `json:"state"`
	Error       string `json:"error,omitempty"`
	ZipURL      string `json:"zip_url,omitempty"`
	ThreeMFURL  string `json:"threemf_url,omitempty"`
	ZipName     string `json:"zip_name,omitempty"`
	ThreeMFName string `json:"threemf_name,omitempty"`
}

var localJobs sync.Map

func jobsBucket() string {
	return strings.TrimSpace(os.Getenv("BAMBU_S3_BUCKET"))
}

func jobsPrefix() string {
	p := strings.Trim(strings.TrimSpace(os.Getenv("JOBS_S3_PREFIX")), "/")
	if p == "" {
		return jobsPrefixDefault
	}
	return p
}

func s3PublicURL(bucket, key string) string {
	region := os.Getenv("AWS_REGION")
	if region == "" {
		region = "us-east-1"
	}
	return "https://" + bucket + ".s3." + region + ".amazonaws.com/" + key
}

func putJobStatus(ctx context.Context, id string, st jobStatus) error {
	body, err := json.Marshal(st)
	if err != nil {
		return err
	}
	localJobs.Store(id, st)
	bucket := jobsBucket()
	if bucket == "" {
		return nil
	}
	cfg, err := config.LoadDefaultConfig(ctx)
	if err != nil {
		return err
	}
	_, err = s3.NewFromConfig(cfg).PutObject(ctx, &s3.PutObjectInput{
		Bucket:       aws.String(bucket),
		Key:          aws.String(jobsPrefix() + "/" + id + "/status.json"),
		Body:         bytes.NewReader(body),
		ContentType:  aws.String("application/json"),
		CacheControl: aws.String("no-store"),
	})
	return err
}

func getJobStatus(ctx context.Context, id string) (jobStatus, bool, error) {
	if v, ok := localJobs.Load(id); ok {
		return v.(jobStatus), true, nil
	}
	bucket := jobsBucket()
	if bucket == "" {
		return jobStatus{}, false, nil
	}
	cfg, err := config.LoadDefaultConfig(ctx)
	if err != nil {
		return jobStatus{}, false, err
	}
	out, err := s3.NewFromConfig(cfg).GetObject(ctx, &s3.GetObjectInput{
		Bucket: aws.String(bucket),
		Key:    aws.String(jobsPrefix() + "/" + id + "/status.json"),
	})
	if err != nil {
		msg := strings.ToLower(err.Error())
		if strings.Contains(msg, "nosuchkey") || strings.Contains(msg, "not found") || strings.Contains(msg, "404") {
			return jobStatus{}, false, nil
		}
		return jobStatus{}, false, err
	}
	defer out.Body.Close()
	b, err := io.ReadAll(out.Body)
	if err != nil {
		return jobStatus{}, false, err
	}
	var st jobStatus
	if err := json.Unmarshal(b, &st); err != nil {
		return jobStatus{}, false, err
	}
	return st, true, nil
}

func putJobBytes(ctx context.Context, key, ctype, filename string, body []byte) (string, error) {
	bucket := jobsBucket()
	if bucket == "" {
		return "", fmt.Errorf("no object store")
	}
	cfg, err := config.LoadDefaultConfig(ctx)
	if err != nil {
		return "", err
	}
	_, err = s3.NewFromConfig(cfg).PutObject(ctx, &s3.PutObjectInput{
		Bucket:             aws.String(bucket),
		Key:                aws.String(key),
		Body:               bytes.NewReader(body),
		ContentType:        aws.String(ctype),
		ContentDisposition: aws.String(`attachment; filename="` + filename + `"`),
	})
	if err != nil {
		return "", err
	}
	return s3PublicURL(bucket, key), nil
}

func startRenderJob(ctx context.Context, l Layout) (string, error) {
	id := uuid.NewString()
	if err := putJobStatus(ctx, id, jobStatus{State: "queued"}); err != nil {
		return "", err
	}
	fn := strings.TrimSpace(os.Getenv("RENDER_FUNCTION_NAME"))
	if fn == "" {
		go func() {
			if err := runRenderJob(context.Background(), id, l); err != nil {
				log.Printf("render job %s: %v", id, err)
			}
		}()
		return id, nil
	}
	payload, err := json.Marshal(renderJob{JobID: id, Layout: l})
	if err != nil {
		return "", err
	}
	cfg, err := config.LoadDefaultConfig(ctx)
	if err != nil {
		return "", err
	}
	_, err = lambda.NewFromConfig(cfg).Invoke(ctx, &lambda.InvokeInput{
		FunctionName:   aws.String(fn),
		InvocationType: lambdatypes.InvocationTypeEvent,
		Payload:        payload,
	})
	if err != nil {
		_ = putJobStatus(ctx, id, jobStatus{State: "error", Error: "could not start render"})
		return "", err
	}
	return id, nil
}

func handleRenderEvent(ctx context.Context, job renderJob) error {
	if job.JobID == "" || !validID(job.JobID) {
		return fmt.Errorf("bad job id")
	}
	normalizeLayout(&job.Layout)
	if err := validateLayout(&job.Layout); err != nil {
		_ = putJobStatus(ctx, job.JobID, jobStatus{State: "error", Error: err.Error()})
		return err
	}
	return runRenderJob(ctx, job.JobID, job.Layout)
}

func runRenderJob(ctx context.Context, id string, l Layout) error {
	_ = putJobStatus(ctx, id, jobStatus{State: "running"})
	if _, ok := openscadAvailable(); !ok {
		err := putJobStatus(ctx, id, jobStatus{State: "error", Error: "this host cannot render STL"})
		if err != nil {
			return err
		}
		return errNoOpenSCAD
	}
	zipBody, err := buildZipBytes(l)
	if err != nil {
		_ = putJobStatus(ctx, id, jobStatus{State: "error", Error: "render failed"})
		return err
	}
	zipName := zipFileName(l.Title)
	threeName := bambuFileName(l.Title)
	threeBody := zipNamedFile(zipBody, "case.3mf")
	if len(threeBody) == 0 {
		_ = putJobStatus(ctx, id, jobStatus{State: "error", Error: "zip has no case.3mf"})
		return fmt.Errorf("zip has no case.3mf")
	}
	zipURL, threeURL, err := storeJobFiles(ctx, id, zipName, threeName, zipBody, threeBody)
	if err != nil {
		_ = putJobStatus(ctx, id, jobStatus{State: "error", Error: "could not store files"})
		return err
	}
	return putJobStatus(ctx, id, jobStatus{
		State:       "ready",
		ZipURL:      zipURL,
		ThreeMFURL:  threeURL,
		ZipName:     zipName,
		ThreeMFName: threeName,
	})
}

func storeJobFiles(ctx context.Context, id, zipName, threeName string, zipBody, threeBody []byte) (zipURL, threeURL string, err error) {
	if jobsBucket() == "" {
		localBlobs.Store(id, jobBlobs{zip: zipBody, three: threeBody})
		base := strings.TrimRight(publicBase(), "/")
		if base == "" {
			base = "http://127.0.0.1:8787"
		}
		return base + "/api/render/" + id + "/zip", base + "/api/render/" + id + "/3mf", nil
	}
	prefix := jobsPrefix() + "/" + id
	zipURL, err = putJobBytes(ctx, prefix+"/panel.zip", "application/zip", zipName, zipBody)
	if err != nil {
		return "", "", err
	}
	threeURL, err = putJobBytes(ctx, prefix+"/case.3mf", "model/3mf", threeName, threeBody)
	return zipURL, threeURL, err
}

func zipNamedFile(zipBody []byte, name string) []byte {
	zr, err := zip.NewReader(bytes.NewReader(zipBody), int64(len(zipBody)))
	if err != nil {
		return nil
	}
	for _, f := range zr.File {
		if f.Name != name {
			continue
		}
		r, err := f.Open()
		if err != nil {
			return nil
		}
		b, err := io.ReadAll(r)
		r.Close()
		if err != nil {
			return nil
		}
		return b
	}
	return nil
}

func handleRenderEventWithTimeout(ctx context.Context, job renderJob) error {
	root := repoRoot()
	if err := os.Chdir(root); err != nil {
		return err
	}
	if err := loadCatalog(root); err != nil {
		log.Printf("catalog: %v", err)
	}
	ctx, cancel := context.WithTimeout(ctx, 14*time.Minute)
	defer cancel()
	return handleRenderEvent(ctx, job)
}
