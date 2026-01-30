package main

import (
	"context"
	"log"
	"os"
	"time"

	"backend/app"
	"backend/database"
	"backend/handlers"
	"backend/internal/sweeper"

	"github.com/joho/godotenv"
)

func main() {
	_ = godotenv.Load()

	dsn := mustEnv("DATABASE_URL")
	secret := mustEnv("JWT_SECRET")

	appBaseURL := getenv("APP_BASE_URL", "http://localhost:3000")
	sweeperIntervalStr := getenv("ITEM_STATUS_SWEEPER_INTERVAL", "1m")
	sweeperInterval, err := time.ParseDuration(sweeperIntervalStr)
	if err != nil {
		log.Fatalf("invalid ITEM_STATUS_SWEEPER_INTERVAL: %v", err)
	}

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	db := app.MustOpenDB(dsn)
	defer db.Close()

	userDatabase := database.NewUserDatabase(db)
	tokenDatabase := database.NewEmailVerificationTokenDatabase(db)
	itemDatabase := database.NewItemDatabase(db)
	pictureDatabase := database.NewPictureDatabase(db)
	bidDatabase := database.NewBidDatabase(db)

	h := handlers.NewHandlerSet(
		userDatabase,
		tokenDatabase,
		itemDatabase,
		pictureDatabase,
		bidDatabase,
		[]byte(secret),
		appBaseURL,
	)

	r := app.NewRouter(h, []byte(secret))

	sweeper.Start(ctx, db, sweeperInterval)

	log.Println("listening on :8080")
	if err := r.Run(":8080"); err != nil {
		log.Fatal(err)
	}
}

func mustEnv(k string) string {
	v := os.Getenv(k)
	if v == "" {
		log.Fatalf("%s is required", k)
	}
	return v
}

func getenv(k, def string) string {
	v := os.Getenv(k)
	if v == "" {
		return def
	}
	return v
}
