package app

import (
	"backend/handlers"
	"backend/middlewares"

	"github.com/gin-gonic/gin"
)

func NewRouter(h *handlers.HandlerSet, jwtSecret []byte, internalToken string) *gin.Engine {
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

	// Upload Image
	r.POST("/uploads/presign", middlewares.RequireAuth(jwtSecret), h.Uploads.PresignPut)

	// Visualization
	r.POST("/visualizations", middlewares.RequireAuth(jwtSecret), h.Visualizations.Create)
	r.GET("/visualizations/:job_id", middlewares.RequireAuth(jwtSecret), h.Visualizations.Get)
	r.PUT("/visualizations/:job_id", middlewares.RequireInternalToken(internalToken), h.Visualizations.UpdateInternal)

	// Bids
	r.POST("/items/:item_id/bids", middlewares.RequireAuth(jwtSecret), h.Bids.PlaceBid)
	r.GET("/items/:item_id/bids", h.Bids.ListBids)

	// Users
	r.GET("/users", h.Users.ListUsers)

	return r
}
