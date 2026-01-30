package handlers

import (
	"backend/database"
)

type HandlerSet struct {
	Auth *AuthHandler
	Items *ItemsHandler
	Bids *BidsHandler
	Users *UserHandler
}

func NewHandlerSet(
	users *database.UserDatabase,
	tokens *database.EmailVerificationTokenDatabase,
	items *database.ItemDatabase,
	pictures *database.PictureDatabase,
	bids *database.BidDatabase,
	jwtSecret []byte,
	appBaseURL string,
) *HandlerSet {
	return &HandlerSet{
		Auth: NewAuthHandler(users, tokens, jwtSecret, appBaseURL),
		Items: NewItemsHandler(items, pictures),
		Bids: NewBidsHandler(bids, items),
		Users: NewUserHandler(users),
	}
}
