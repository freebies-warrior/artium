package app

import (
	"backend/handlers"

	"github.com/gin-gonic/gin"
)

func NewRouter(h *handlers.HandlerSet) *gin.Engine {
	r := gin.New()
	r.Use(gin.Logger(), gin.Recovery())

	// Auth endpoints
	r.POST("/auth/signup", h.Auth.Signup)
	r.POST("/auth/login", h.Auth.Login)

	// Verification
	r.POST("/auth/verify", h.Auth.VerifyEmail)
	r.POST("/auth/resend-verification", h.Auth.ResendVerification)

	return r
}
