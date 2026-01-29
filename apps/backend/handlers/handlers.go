package handlers

import "backend/database"
import "github.com/aws/aws-sdk-go-v2/service/s3"

type HandlerSet struct {
	Auth *AuthHandler
	Items *ItemsHandler
	Uploads *UploadHandler
	Bids *BidsHandler
}

func NewHandlerSet(
	users *database.UserDatabase,
	tokens *database.EmailVerificationTokenDatabase,
	items *database.ItemDatabase,
	pictures *database.PictureDatabase,
	bids *database.BidDatabase,
	jwtSecret []byte,
	appBaseURL string,
	r2Bucket string,
	s3Client *s3.Client,
) *HandlerSet {
	return &HandlerSet{
		Auth: NewAuthHandler(users, tokens, jwtSecret, appBaseURL),
		Items: NewItemsHandler(items, pictures),
		Uploads: NewUploadHandler(r2Bucket, s3Client),
		Bids: NewBidsHandler(bids, items),
	}
}
