package middleware

import (
	"net/http"
	"strings"

	"backend/utils"

	"github.com/gin-gonic/gin"
)

const CtxUserIDKey = "user_id"
const CtxEmailKey = "user_email"

func RequireAuth(jwtSecret []byte) gin.HandlerFunc {
	return func(c *gin.Context) {
		auth := c.GetHeader("Authorization")
		if !strings.HasPrefix(auth, "Bearer ") {
			c.JSON(http.StatusUnauthorized, utils.NewError("UNAUTHORIZED", "missing bearer token", nil))
			c.Abort()
			return
		}

		tokenStr := strings.TrimPrefix(auth, "Bearer ")
		claims, err := utils.VerifyJWT(jwtSecret, tokenStr)
		if err != nil {
			c.JSON(http.StatusUnauthorized, utils.NewError("UNAUTHORIZED", "invalid token", nil))
			c.Abort()
			return
		}

		c.Set(CtxUserIDKey, claims.UID)
		c.Set(CtxEmailKey, claims.Email)
		c.Next()
	}
}
