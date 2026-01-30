package main

import (
	"context"
	"log"
	"os"
	"path/filepath"
	"runtime"
	"strings"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/joho/godotenv"
)

func main() {
	_ = godotenv.Load()
	dsn := os.Getenv("DATABASE_URL")
	if dsn == "" {
		log.Fatal("DATABASE_URL is not set")
	}

	root := projectRoot()

	sqlFiles := []string{
		// Extensions
		"apps/backend/migrations/extensions/pgcrypto.sql",

		// Tables
		"apps/backend/migrations/tables/users.sql",
		"apps/backend/migrations/tables/email_verification_tokens.sql",
		"apps/backend/migrations/tables/items.sql",
		"apps/backend/migrations/tables/pictures.sql",
		"apps/backend/migrations/tables/bids.sql",

		// Functions / Procedures
		"apps/backend/migrations/functions/tg_set_updated_at.sql",
		"apps/backend/migrations/functions/validate_bid_before_insert.sql",
		"apps/backend/migrations/functions/update_item_highest_bid_after_insert.sql",

		// Triggers
		"apps/backend/migrations/triggers/users_set_updated_at.sql",
		"apps/backend/migrations/triggers/items_set_updated_at.sql",
		"apps/backend/migrations/triggers/trg_validate_bid_before_insert.sql",
		"apps/backend/migrations/triggers/trg_update_item_highest_bid_after_insert.sql",
	}

	ctx := context.Background()
	pool, err := pgxpool.New(ctx, dsn)
	if err != nil {
		log.Fatalf("connect: %v", err)
	}
	defer pool.Close()

	tx, err := pool.Begin(ctx)
	if err != nil {
		log.Fatalf("begin tx: %v", err)
	}
	defer func() { _ = tx.Rollback(ctx) }()

	// Reset schema
	resetSQL := `
		DROP SCHEMA IF EXISTS public CASCADE;
		CREATE SCHEMA public;
		GRANT ALL ON SCHEMA public TO postgres;
		GRANT ALL ON SCHEMA public TO public;
	`
	if _, err := tx.Exec(ctx, resetSQL); err != nil {
		log.Fatalf("reset schema failed: %v", err)
	}

	// Apply SQL in the exact order above
	for _, rel := range sqlFiles {
		abs := filepath.Join(root, filepath.FromSlash(rel))
		b, err := os.ReadFile(abs)
		if err != nil {
			log.Fatalf("read %s: %v", rel, err)
		}
		sql := strings.TrimSpace(string(b))
		if sql == "" {
			continue
		}

		log.Printf("-> %s", rel)
		if _, err := tx.Exec(ctx, sql); err != nil {
			log.Fatalf("exec failed in %s: %v", rel, err)
		}
	}

	if err := tx.Commit(ctx); err != nil {
		log.Fatalf("commit: %v", err)
	}
	log.Println("DB reset + rebuild complete ✅")
}

func projectRoot() string {
	_, file, _, ok := runtime.Caller(0)
	if !ok {
		wd, _ := os.Getwd()
		return wd
	}
	dir := filepath.Dir(file)
	return filepath.Clean(filepath.Join(dir, "../../../.."))
}
