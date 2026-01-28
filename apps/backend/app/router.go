package app

import (
	"backend/handlers"
	"backend/middlewares"

	"github.com/gin-gonic/gin"
)

func NewRouter(h *handlers.HandlerSet, jwtSecret []byte) *gin.Engine {
	r := gin.New()
	r.Use(gin.Logger(), gin.Recovery())

	r.Use(middlewares.CORS([]string{
		"http://localhost:3000",
	}))

	// Auth
	r.POST("/auth/signup", h.Auth.Signup)
	r.POST("/auth/login", h.Auth.Login)

	// Verification
	r.POST("/auth/verify", h.Auth.VerifyEmail)
	r.POST("/auth/resend-verification", h.Auth.ResendVerification)

	// Items
	r.GET("/items", h.Items.ListItems)
	r.GET("/items/:item_id", h.Items.GetItem)
	r.POST("/items", middlewares.RequireAuth(jwtSecret), h.Items.PostItem)

	return r
}
