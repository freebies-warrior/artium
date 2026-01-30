package main

import (
	"log"
	"os"

	"backend/app"
	"backend/database"
	"backend/handlers"
	"backend/utils/email"

	"github.com/joho/godotenv"
)

func main() {
	_ = godotenv.Load()

	dsn := mustEnv("DATABASE_URL")
	secret := mustEnv("JWT_SECRET")

	appBaseURL := getenv("APP_BASE_URL", "http://localhost:3000")

	emailService := email.New(email.Config{
		Host:     mustEnv("SMTP_HOST"),
		Port:     587, // keep simple for now
		Username: mustEnv("SMTP_USERNAME"),
		Password: mustEnv("SMTP_PASSWORD"),
		FromName: mustEnv("EMAIL_FROM_NAME"),
		FromAddr: mustEnv("EMAIL_FROM_ADDRESS"),
	})

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
		emailService,
		[]byte(secret),
		appBaseURL,
	)

	r := app.NewRouter(h, []byte(secret))

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
