package handlers

import "backend/database"

type HandlerSet struct {
	Auth  *AuthHandler
	Items *ItemsHandler
}

func NewHandlerSet(
	users *database.UserDatabase,
	tokens *database.EmailVerificationTokenDatabase,
	items *database.ItemDatabase,
	pictures *database.PictureDatabase,
	jwtSecret []byte,
	appBaseURL string,
) *HandlerSet {
	return &HandlerSet{
		Auth:  NewAuthHandler(users, tokens, jwtSecret, appBaseURL),
		Items: NewItemsHandler(items, pictures),
	}
}
