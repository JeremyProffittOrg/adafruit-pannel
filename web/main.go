package main

import (
	"context"
	"log"
	"os"
	"path/filepath"
	"strings"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
	fiberadapter "github.com/awslabs/aws-lambda-go-api-proxy/fiber"
	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/logger"
	"github.com/gofiber/fiber/v2/middleware/recover"
)

var (
	store   *Store
	adapter *fiberadapter.FiberLambda
)

func repoRoot() string {
	if v := os.Getenv("LAMBDA_TASK_ROOT"); v != "" {
		return v
	}
	wd, _ := os.Getwd()
	if _, err := os.Stat(filepath.Join(wd, "cad", "case.scad")); err == nil {
		return wd
	}
	if _, err := os.Stat(filepath.Join(wd, "..", "cad", "case.scad")); err == nil {
		return filepath.Join(wd, "..")
	}
	return wd
}

func newApp() *fiber.App {
	app := fiber.New(fiber.Config{
		BodyLimit: 2 << 20,
	})
	app.Use(recover.New())
	app.Use(func(c *fiber.Ctx) error {
		c.Set("X-Content-Type-Options", "nosniff")
		c.Set("X-Frame-Options", "DENY")
		c.Set("Referrer-Policy", "no-referrer")
		c.Set("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; worker-src 'self' blob:; frame-ancestors 'none'")
		if strings.HasPrefix(publicBase(), "https://") {
			c.Set("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
		}
		p := c.Path()
		if strings.HasPrefix(p, "/api/") || p == "/" || p == "/login" || p == "/logout" || strings.HasPrefix(p, "/auth/") || strings.HasSuffix(p, ".html") || strings.HasSuffix(p, ".js") || strings.HasSuffix(p, ".css") {
			c.Set("Cache-Control", "no-store, private")
		} else {
			c.Set("Cache-Control", "public, max-age=86400")
		}
		return c.Next()
	})
	if os.Getenv("AWS_LAMBDA_FUNCTION_NAME") == "" {
		app.Use(logger.New())
	}

	root := repoRoot()
	staticDir := filepath.Join(root, "web", "static")
	if os.Getenv("LAMBDA_TASK_ROOT") != "" {
		staticDir = filepath.Join(root, "static")
	}
	app.Static("/", staticDir)

	app.Get("/login", handleLogin)
	app.Get("/logout", handleLogout)
	app.Get("/auth/amazon/callback", handleLWACallback)

	app.Get("/api/me", handleMe)
	app.Get("/api/devices", handleDevices)
	app.Post("/api/generate", handleGenerate)
	app.Post("/api/bom", handleBOM)

	api := app.Group("/api", requireUser)
	api.Get("/folders", handleFolders)
	api.Post("/folders", handleFolders)
	api.Put("/folders/:id", handleFolder)
	api.Delete("/folders/:id", handleFolder)
	api.Get("/cases", handleCases)
	api.Post("/cases", handleCases)
	api.Get("/cases/:id", handleCase)
	api.Put("/cases/:id", handleCase)
	api.Delete("/cases/:id", handleCase)
	api.Get("/cases/:id/notes", handleNotes)
	api.Post("/cases/:id/notes", handleNotes)
	api.Delete("/cases/:id/notes/:nid", handleNoteDelete)
	api.Get("/search", handleSearch)
	api.Get("/parts/:part/cases", handleCasesByPart)
	return app
}

func lambdaHandler(ctx context.Context, req events.APIGatewayV2HTTPRequest) (events.APIGatewayV2HTTPResponse, error) {
	return adapter.ProxyWithContextV2(ctx, req)
}

func main() {
	root := repoRoot()
	if err := os.Chdir(root); err != nil {
		log.Fatal(err)
	}
	if err := loadCatalog(root); err != nil {
		log.Printf("catalog: %v", err)
	}
	ctx := context.Background()
	st, err := newStore(ctx)
	if err != nil {
		log.Fatal(err)
	}
	store = st
	app := newApp()
	if os.Getenv("AWS_LAMBDA_FUNCTION_NAME") != "" {
		adapter = fiberadapter.New(app)
		lambda.Start(lambdaHandler)
		return
	}
	addr := ":8787"
	if p := os.Getenv("PORT"); p != "" {
		addr = ":" + p
	}
	log.Printf("panel web  http://127.0.0.1%s", addr)
	log.Fatal(app.Listen(addr))
}
