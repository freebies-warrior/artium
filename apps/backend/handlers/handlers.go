package handlers

import (
	"backend/database"
	"backend/utils/email"
)

type HandlerSet struct {
	Auth *AuthHandler
	Items *ItemsHandler
	Bids *BidsHandler
}

func NewHandlerSet(
	users *database.UserDatabase,
	tokens *database.EmailVerificationTokenDatabase,
	items *database.ItemDatabase,
	pictures *database.PictureDatabase,
	bids *database.BidDatabase,
	emailService *email.Service,
	jwtSecret []byte,
	appBaseURL string,
) *HandlerSet {
	return &HandlerSet{
		Auth: NewAuthHandler(users, tokens, emailService, jwtSecret, appBaseURL),
		Items: NewItemsHandler(items, pictures),
		Bids: NewBidsHandler(bids, items),
	}
}
