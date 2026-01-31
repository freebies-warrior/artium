package handlers

import (
	"context"
	"log"
	"net/http"
	"regexp"
	"strings"
	"time"

	"backend/database"
	"backend/utils"
	"backend/utils/email"

	"github.com/gin-gonic/gin"
)

type AuthHandler struct {
	users      *database.UserDatabase
	tokens     *database.EmailVerificationTokenDatabase
	email      *email.Service
	jwtSecret  []byte
	appBaseURL string
}

func NewAuthHandler(
	users *database.UserDatabase,
	tokens *database.EmailVerificationTokenDatabase,
	emailService *email.Service,
	jwtSecret []byte,
	appBaseURL string,
) *AuthHandler {
	return &AuthHandler{
		users:      users,
		tokens:     tokens,
		email:      emailService,
		jwtSecret:  jwtSecret,
		appBaseURL: appBaseURL,
	}
}

type signupReq struct {
	Email    string `json:"email"`
	Username string `json:"username"`
	Password string `json:"password"`
}

type loginReq struct {
	Email    string `json:"email"`
	Password string `json:"password"`
}

type verifyReq struct {
	Token string `json:"token"`
}

type resendReq struct {
	Email string `json:"email"`
}

type signupResp struct {
	User database.UserPublic `json:"user"`
}

type loginResp struct {
	Token string              `json:"token"`
	User  database.UserPublic `json:"user"`
}

type verifyResp struct {
	User database.UserPublic `json:"user"`
}

type okResp struct {
	OK bool `json:"ok"`
}

var emailRe = regexp.MustCompile(`^[^@\s]+@[^@\s]+\.[^@\s]+$`)
var usernameRe = regexp.MustCompile(`^[a-z0-9_]{3,20}$`)

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

	username := normalizeUsername(req.Username)
	if !usernameRe.MatchString(username) {
		c.JSON(http.StatusBadRequest,
			utils.NewError("VALIDATION_ERROR", "invalid username (3-20 chars: a-z, 0-9, _)",
				map[string]any{"field": "username"},
			),
		)
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

	u, err := h.users.CreateUser(c.Request.Context(), email, username, hash)
	if err != nil {
		if constraint, ok := database.UniqueViolationConstraint(err); ok {
			// Postgres default constraint for "field unique" is usually "users_field_key"
			switch constraint {
			case "users_email_key":
				c.JSON(http.StatusConflict, utils.NewError("CONFLICT", "email already exists", map[string]any{"field": "email"}))
				return
			case "users_username_key":
				c.JSON(http.StatusConflict, utils.NewError("CONFLICT", "username already exists", map[string]any{"field": "username"}))
				return
			default:
				c.JSON(http.StatusConflict, utils.NewError("CONFLICT", "email or username already exists", nil))
				return
			}
		}
		c.JSON(http.StatusInternalServerError, utils.NewError("INTERNAL_ERROR", "database error", nil))
		return
	}

	if err := h.sendVerificationLink(c.Request.Context(), u.ID, u.Email); err != nil {
		c.JSON(http.StatusInternalServerError, utils.NewError("INTERNAL_ERROR", "failed to send verification link", nil))
		return
	}

	c.JSON(http.StatusCreated, signupResp{User: u})
}

func (h *AuthHandler) Login(c *gin.Context) {
	var req loginReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "invalid json", nil))
		return
	}

	email := normalizeEmail(req.Email)
	if email == "" || req.Password == "" {
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "email and password required", nil))
		return
	}

	row, err := h.users.GetUserByEmail(c.Request.Context(), email)
	if err != nil || !utils.CheckPassword(row.PasswordHash, req.Password) {
		c.JSON(http.StatusUnauthorized, utils.NewError("UNAUTHORIZED", "wrong credentials", nil))
		return
	}

	if !row.Verified {
		c.JSON(http.StatusForbidden, utils.NewError(
			"FORBIDDEN",
			"please verify your email before logging in",
			map[string]any{"reason": "EMAIL_NOT_VERIFIED"},
		))
		return
	}

	token, err := utils.SignJWT(h.jwtSecret, row.ID, row.Email, 24*time.Hour)
	if err != nil {
		c.JSON(http.StatusInternalServerError, utils.NewError("INTERNAL_ERROR", "failed to create token", nil))
		return
	}

	c.JSON(http.StatusOK, loginResp{
		Token: token,
		User: database.UserPublic{
			ID: row.ID, Email: row.Email, Username: row.Username, Verified: row.Verified,
		},
	})
}

func (h *AuthHandler) VerifyEmail(c *gin.Context) {
	var req verifyReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "invalid json", nil))
		return
	}
	if strings.TrimSpace(req.Token) == "" {
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "token required", map[string]any{"field": "token"}))
		return
	}

	tokenHash := utils.HashVerificationToken(req.Token)

	u, err := h.tokens.VerifyToken(c.Request.Context(), tokenHash)
	if err != nil {
		if err == database.ErrInvalidOrExpiredToken {
			c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "invalid or expired token", nil))
			return
		}
		c.JSON(http.StatusInternalServerError, utils.NewError("INTERNAL_ERROR", "database error", nil))
		return
	}

	c.JSON(http.StatusOK, verifyResp{User: u})
}

func (h *AuthHandler) ResendVerification(c *gin.Context) {
	var req resendReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "invalid json", nil))
		return
	}

	email := normalizeEmail(req.Email)
	if !emailRe.MatchString(email) {
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "invalid email", map[string]any{"field": "email"}))
		return
	}

	row, err := h.users.GetUserByEmail(c.Request.Context(), email)
	if err != nil {
		c.JSON(http.StatusInternalServerError, okResp{OK: false})
		return
	}

	if row.Verified {
		c.JSON(http.StatusBadRequest, okResp{OK: false})
		return
	}

	if err := h.sendVerificationLink(c.Request.Context(), row.ID, row.Email); err != nil {
		c.JSON(http.StatusInternalServerError, utils.NewError("INTERNAL_ERROR", "failed to send verification link", nil))
		return
	}

	c.JSON(http.StatusOK, okResp{OK: true})
}

func (h *AuthHandler) sendVerificationLink(ctx context.Context, userID, email string) error {
	rawToken, tokenHash, err := utils.GenerateVerificationToken()
	if err != nil {
		return err
	}

	// Invalidate any old tokens
	_ = h.tokens.InvalidateUnusedTokens(ctx, userID)

	expires := time.Now().Add(1 * time.Hour)
	if err := h.tokens.CreateToken(ctx, userID, tokenHash, expires); err != nil {
		log.Printf("error")
		return err
	}

	verifyURL := h.appBaseURL + "/verify?token=" + rawToken

	expiryMinutes := int(time.Until(expires).Minutes())

	if err := h.email.SendVerificationEmail(
		email,
		verifyURL,
		expiryMinutes,
	); err != nil {
		log.Printf(
			"failed to send verification email user_id=%s err=%v",
			userID,
			err,
		)
		return err
	}

	return nil
}

func normalizeEmail(s string) string {
	return strings.ToLower(strings.TrimSpace(s))
}

func normalizeUsername(s string) string {
	return strings.ToLower(strings.TrimSpace(s))
}
