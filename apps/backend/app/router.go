package app

import (
	"backend/handlers"
	"backend/middlewares"

	"github.com/gin-gonic/gin"
)

func NewRouter(h *handlers.HandlerSet) *gin.Engine {
	r := gin.New()
	r.Use(gin.Logger(), gin.Recovery())

	r.Use(middlewares.CORS([]string{
		"http://localhost:3000",
	}))

	// Auth endpoints
	r.POST("/auth/signup", h.Auth.Signup)
	r.POST("/auth/login", h.Auth.Login)

	// Verification
	r.POST("/auth/verify", h.Auth.VerifyEmail)
	r.POST("/auth/resend-verification", h.Auth.ResendVerification)

	return r
}
