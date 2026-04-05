package main

import (
	"log"
	"net/http"
	"os"
	"path/filepath"

	"cashcompass-server/internal/app"
	"cashcompass-server/internal/db"
	"cashcompass-server/internal/web"
)

func main() {
	dataDir := filepath.Join(".", "data")
	if err := os.MkdirAll(dataDir, 0o755); err != nil {
		log.Fatalf("data dir: %v", err)
	}

	dbPath := os.Getenv("CASHCOMPASS_DB_PATH")
	if dbPath == "" {
		dbPath = filepath.Join(dataDir, "cashcompass.db")
	}
	log.Printf("db: opening %s", dbPath)

	sqlDB, err := db.Open(dbPath)
	if err != nil {
		log.Fatalf("db open: %v", err)
	}
	defer sqlDB.Close()

	migrateResult, err := db.Migrate(sqlDB)
	if err != nil {
		log.Fatalf("db migrate: %v", err)
	}
	if len(migrateResult.Applied) > 0 {
		log.Printf("db: applied migrations %v", migrateResult.Applied)
	}
	if len(migrateResult.Skipped) > 0 {
		log.Printf("db: already applied migrations %v (skipped)", migrateResult.Skipped)
	}
	if len(migrateResult.Applied) == 0 && len(migrateResult.Skipped) == 0 {
		log.Printf("db: no migrations defined")
	}

	seeded, err := db.SeedIfEmpty(sqlDB)
	if err != nil {
		log.Fatalf("db seed: %v", err)
	}
	if seeded {
		log.Printf("db: seeded with sample data")
	}

	templates, err := web.ParseTemplates()
	if err != nil {
		log.Fatalf("templates: %v", err)
	}
	log.Printf("templates: parsed %d templates", len(templates.Templates()))

	devMode := os.Getenv("CASHCOMPASS_DEV") == "true"
	if devMode {
		log.Printf("dev mode enabled")
	}
	server := &app.Server{DB: sqlDB, Templates: templates, DevMode: devMode}
	port := os.Getenv("CASHCOMPASS_PORT")
	if port == "" {
		port = "8080"
	}
	addr := ":" + port
	log.Printf("cashcompass server listening on %s", addr)
	if err := http.ListenAndServe(addr, server.Routes()); err != nil {
		log.Fatalf("server: %v", err)
	}
}
