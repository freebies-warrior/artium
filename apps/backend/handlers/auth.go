package handlers

import (
	"net/http"
	"regexp"
	"strings"

	"backend/utils"
	"backend/database"

	"github.com/gin-gonic/gin"
)

type AuthHandler struct {
	users     *database.UserDatabase
	jwtSecret []byte
}

func NewAuthHandler(users *database.UserDatabase, jwtSecret []byte) *AuthHandler {
	return &AuthHandler{users: users, jwtSecret: jwtSecret}
}

type signupReq struct {
	Email    string `json:"email"`
	Password string `json:"password"`
}

type loginReq struct {
	Email    string `json:"email"`
	Password string `json:"password"`
}

type signupResp struct {
	User database.UserPublic `json:"user"`
}

type loginResp struct {
	Token string          `json:"token"`
	User  database.UserPublic `json:"user"`
}

var emailRe = regexp.MustCompile(`^[^@\s]+@[^@\s]+\.[^@\s]+$`)

func (h *AuthHandler) Signup(c *gin.Context) {
	var req signupReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "invalid json", nil))
		return
	}

	email := normalizeEmail(req.Email)
	if !emailRe.MatchString(email) {
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "invalid email", map[string]any{"field": "email"}))
		return
	}
	if len(req.Password) < 8 {
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "password must be at least 8 characters", map[string]any{"field": "password"}))
		return
	}

	hash, err := utils.HashPassword(req.Password)
	if err != nil {
		c.JSON(http.StatusInternalServerError, utils.NewError("INTERNAL_ERROR", "failed to hash password", nil))
		return
	}

	u, err := h.users.CreateUser(c.Request.Context(), email, hash)
	if err != nil {
		if database.IsUniqueViolation(err) {
			c.JSON(http.StatusConflict, utils.NewError("CONFLICT", "email already exists", map[string]any{"field": "email"}))
			return
		}
		c.JSON(http.StatusInternalServerError, utils.NewError("INTERNAL_ERROR", "database error", nil))
		return
	}

	c.JSON(http.StatusCreated, signupResp{User: u})
}

func normalizeEmail(s string) string {
	return strings.ToLower(strings.TrimSpace(s))
}
