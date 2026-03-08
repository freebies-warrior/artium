package handlers

import (
	"backend/database"
	"backend/utils"
	"net/http"
	"strconv"
	"strings"

	"github.com/gin-gonic/gin"
)

type UserHandler struct {
	users *database.UserDatabase
}

func NewUserHandler(users *database.UserDatabase) *UserHandler {
	return &UserHandler{
		users: users,
	}
}

type listUsersResp struct {
	Data       []database.PublicUserDetails `json:"data"`
	NextCursor *string                      `json:"next_cursor"`
}

func (h *UserHandler) ListUsers(c *gin.Context) {
	ctx := c.Request.Context()

	// ---------- limit ----------
	limit := 20
	if s := strings.TrimSpace(c.Query("limit")); s != "" {
		n, err := strconv.Atoi(s)
		if err != nil {
			c.JSON(http.StatusBadRequest, utils.NewError(
				"VALIDATION_ERROR",
				"invalid limit",
				map[string]any{"field": "limit"},
			))
			return
		}
		limit = n
	}

	// ---------- params ----------
	params := database.ListUsersParams{
		Limit:  limit,
		Query:  strings.TrimSpace(c.Query("q")),
		Cursor: strings.TrimSpace(c.Query("cursor")),
	}

	// ---------- database ----------
	users, nextCursor, err := h.users.ListUsers(ctx, params)
	if err != nil {
		c.JSON(http.StatusBadRequest, utils.NewError(
			"VALIDATION_ERROR",
			"invalid query params",
			nil,
		))
		return
	}

	// ---------- response ----------
	c.JSON(http.StatusOK, listUsersResp{
		Data:       users,
		NextCursor: nextCursor,
	})
}

func (h *UserHandler) GetUserDetails(c *gin.Context) {
	userID := strings.TrimSpace(c.Param("user_id"))
	if userID == "" {
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "user_id required", nil))
		return
	}
	if !isUUID(userID) {
		invalidUUIDResponse(c, "user_id")
		return
	}

	u, err := h.users.GetUserDetailsByUserID(c.Request.Context(), userID)
	if err != nil {
		if err == database.ErrNotFound {
			c.JSON(http.StatusNotFound, utils.NewError("NOT_FOUND", "user not found", nil))
			return
		}
		if handleInvalidUUIDDBError(c, err, "user_id") {
			return
		}
		c.JSON(http.StatusInternalServerError, utils.NewError("INTERNAL_ERROR", "database error", nil))
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"email":    u.Email,
		"username": u.Username,
	})
}
