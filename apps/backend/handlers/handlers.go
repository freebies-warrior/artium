package handlers

import (
	"backend/database"
	"backend/utils/email"

	"github.com/aws/aws-sdk-go-v2/service/s3"
)

type HandlerSet struct {
	Auth           *AuthHandler
	Items          *ItemsHandler
	Uploads        *UploadHandler
	Bids           *BidsHandler
	Users          *UserHandler
	Visualizations *VisualizationsHandler
}

func NewHandlerSet(
	users *database.UserDatabase,
	tokens *database.EmailVerificationTokenDatabase,
	items *database.ItemDatabase,
	pictures *database.PictureDatabase,
	bids *database.BidDatabase,
	visualizationJobs *database.VisualizationJobDatabase,
	emailService *email.Service,
	jwtSecret []byte,
	appBaseURL string,
	backendBaseURL string,
	aiBaseURL string,
	aiToken string,
	r2Bucket string,
	s3Client *s3.Client,
) *HandlerSet {
	uploadHandler := NewUploadHandler(r2Bucket, s3Client)
	visualizerClient := NewVisualizerClient(aiBaseURL, aiToken)
	featureExtractorClient := NewFeatureExtractorClient(aiBaseURL, aiToken)

	return &HandlerSet{
		Auth:           NewAuthHandler(users, tokens, emailService, jwtSecret, appBaseURL),
		Items:          NewItemsHandler(items, pictures, uploadHandler, featureExtractorClient, backendBaseURL),
		Uploads:        uploadHandler,
		Bids:           NewBidsHandler(bids, items),
		Users:          NewUserHandler(users),
		Visualizations: NewVisualizationsHandler(visualizationJobs, uploadHandler, visualizerClient),
	}
}
