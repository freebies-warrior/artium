package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"strconv"
	"time"

	"backend/app"
	"backend/database"
	"backend/handlers"
	"backend/internal/sweeper"
	"backend/utils/email"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/credentials"
	"github.com/aws/aws-sdk-go-v2/service/s3"
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
	smtpPort, err := strconv.Atoi(mustEnv("SMTP_PORT"))
	if err != nil {
		log.Fatalf("invalid SMTP_PORT: %v", err)
	}

	emailService := email.New(email.Config{
		Host:     mustEnv("SMTP_HOST"),
		Port:     smtpPort,
		Username: getenv("SMTP_USERNAME", ""),
		Password: getenv("SMTP_PASSWORD", ""),
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

	r2AccountID := mustEnv("R2_ACCOUNT_ID")
	r2AccessKey := mustEnv("R2_ACCESS_KEY_ID")
	r2SecretKey := mustEnv("R2_SECRET_ACCESS_KEY")
	r2Bucket := mustEnv("R2_BUCKET")

	storageEndpoint := fmt.Sprintf("https://%s.r2.cloudflarestorage.com", r2AccountID)

	endpointResolver := aws.EndpointResolverWithOptionsFunc(func(service, region string, options ...any) (aws.Endpoint, error) {
		if service == s3.ServiceID {
			return aws.Endpoint{
				URL:               storageEndpoint,
				SigningRegion:     "auto",
				HostnameImmutable: true,
			}, nil
		}
		return aws.Endpoint{}, &aws.EndpointNotFoundError{}
	})

	cfg, err := config.LoadDefaultConfig(
		context.Background(),
		config.WithRegion("auto"),
		config.WithCredentialsProvider(credentials.NewStaticCredentialsProvider(r2AccessKey, r2SecretKey, "")),
		config.WithEndpointResolverWithOptions(endpointResolver),
	)
	if err != nil {
		log.Fatal(err)
	}

	s3Client := s3.NewFromConfig(cfg, func(o *s3.Options) {
		o.UsePathStyle = true
	})

	h := handlers.NewHandlerSet(
		userDatabase,
		tokenDatabase,
		itemDatabase,
		pictureDatabase,
		bidDatabase,
		emailService,
		[]byte(secret),
		appBaseURL,
		r2Bucket,
		s3Client,
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
