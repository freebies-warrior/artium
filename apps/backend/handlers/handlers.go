package handlers

import "backend/database"

type HandlerSet struct {
	Auth *AuthHandler
}

func NewHandlerSet(users *database.UserDatabase, jwtSecret []byte) *HandlerSet {
	return &HandlerSet{
		Auth: NewAuthHandler(users, jwtSecret),
	}
}
