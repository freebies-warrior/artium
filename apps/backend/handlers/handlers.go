package handlers

import "backend/database"

type HandlerSet struct {
	Auth *AuthHandler
}

func NewHandlerSet(
	users *database.UserDatabase,
	tokens *database.EmailVerificationTokenDatabase,
	jwtSecret []byte,
	appBaseURL string,
) *HandlerSet {
	return &HandlerSet{
		Auth: NewAuthHandler(users, tokens, jwtSecret, appBaseURL),
	}
}
