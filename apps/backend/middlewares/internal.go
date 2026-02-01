package middlewares

import (
	"net/http"
	"strings"

	"backend/utils"

	"github.com/gin-gonic/gin"
)

func RequireInternalToken(token string) gin.HandlerFunc {
	return func(c *gin.Context) {
		if strings.TrimSpace(token) == "" {
			c.JSON(http.StatusInternalServerError, utils.NewError("INTERNAL_ERROR", "internal token not configured", nil))
			c.Abort()
			return
		}

		// Prefer Authorization: Bearer <token>
		auth := c.GetHeader("Authorization")
		if strings.HasPrefix(auth, "Bearer ") {
			got := strings.TrimSpace(strings.TrimPrefix(auth, "Bearer "))
			if got == token {
				c.Next()
				return
			}
		}

		// Optional alternative header
		if c.GetHeader("X-Internal-Token") == token {
			c.Next()
			return
		}

		c.JSON(http.StatusUnauthorized, utils.NewError("UNAUTHORIZED", "invalid internal token", nil))
		c.Abort()
	}
}
