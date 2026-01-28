package handlers

import "backend/database"

type HandlerSet struct {
	Auth *AuthHandler
	Bids *BidsHandler
	JWTSecret []byte
}

func NewHandlerSet(
	users *database.UserDatabase,
	tokens *database.EmailVerificationTokenDatabase,
	bids *database.BidDatabase,
	items *database.ItemDatabase,
	jwtSecret []byte,
	appBaseURL string,
) *HandlerSet {
	return &HandlerSet{
		Auth: NewAuthHandler(users, tokens, jwtSecret, appBaseURL),
		Bids: NewBidsHandler(bids, items),
		JWTSecret: jwtSecret,
	}
}
