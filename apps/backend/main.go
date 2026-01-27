package main

import (
	"log"
	"os"

	"backend/app"
	"backend/handlers"
	"backend/database"
)

func main() {
	dsn := mustEnv("DATABASE_URL")
	secret := mustEnv("JWT_SECRET")

	db := app.MustOpenDB(dsn)
	defer db.Close()

	userDatabase := database.NewUserDatabase(db)

	h := handlers.NewHandlerSet(userDatabase, []byte(secret))
	r := app.NewRouter(h)

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
