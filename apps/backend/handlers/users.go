package handlers

import (
	"database/sql"
	"encoding/base64"
	"encoding/json"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
)

type UserHandler struct {
	db *sql.DB
}

func NewUserHandler(db *sql.DB) *UserHandler {
	return &UserHandler{
		db: db,
	}
}

type PublicUser struct {
	ID        string    `json:"id"`
	Username  string    `json:"username"`
	Verified  bool      `json:"verified"`
	CreatedAt time.Time `json:"created_at"`
}

type UserCursor struct {
	CreatedAt time.Time `json:"created_at"`
	ID        string    `json:"id"`
}

func encodeCursor(c UserCursor) (string, error) {
	b, err := json.Marshal(c)
	if err != nil {
		return "", err
	}
	return base64.StdEncoding.EncodeToString(b), nil
}

func decodeCursor(s string) (*UserCursor, error) {
	b, err := base64.StdEncoding.DecodeString(s)
	if err != nil {
		return nil, err
	}
	var c UserCursor
	if err := json.Unmarshal(b, &c); err != nil {
		return nil, err
	}
	return &c, nil
}

func (h *UserHandler) ListUsers(c *gin.Context) {
	ctx := c.Request.Context()

	// ---------- limit ----------
	limit := 20
	if l := c.Query("limit"); l != "" {
		if v, err := strconv.Atoi(l); err == nil && v > 0 {
			if v > 100 {
				v = 100
			}
			limit = v
		}
	}

	// ---------- search ----------
	search := strings.TrimSpace(c.Query("q"))

	// ---------- cursor ----------
	var cursor *UserCursor
	if cursorStr := c.Query("cursor"); cursorStr != "" {
		decoded, err := decodeCursor(cursorStr)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{
				"error": "invalid cursor",
			})
			return
		}
		cursor = decoded
	}

	// ---------- SQL ----------
	query := `
		SELECT id::text, username, verified, created_at
		FROM users
		WHERE 1=1
	`

	args := []any{}
	argID := 1

	if search != "" {
		query += " AND username ILIKE $" + strconv.Itoa(argID)
		args = append(args, "%"+search+"%")
		argID++
	}

	if cursor != nil {
		query += `
			AND (
				created_at < $` + strconv.Itoa(argID) + `
				OR (
					created_at = $` + strconv.Itoa(argID) + `
					AND id < $` + strconv.Itoa(argID+1) + `
				)
			)
		`
		args = append(args, cursor.CreatedAt, cursor.ID)
		argID += 2
	}

	query += `
		ORDER BY created_at DESC, id DESC
		LIMIT $` + strconv.Itoa(argID)
	args = append(args, limit+1)

	// ---------- execute ----------
	rows, err := h.db.QueryContext(ctx, query, args...)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "failed to list users",
		})
		return
	}
	defer rows.Close()

	var users []PublicUser
	for rows.Next() {
		var u PublicUser
		if err := rows.Scan(
			&u.ID,
			&u.Username,
			&u.Verified,
			&u.CreatedAt,
		); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{
				"error": "failed to scan user",
			})
			return
		}
		users = append(users, u)
	}

	// ---------- pagination ----------
	var nextCursor *string
	if len(users) > limit {
		last := users[limit-1]
		cur, _ := encodeCursor(UserCursor{
			CreatedAt: last.CreatedAt,
			ID:        last.ID,
		})
		nextCursor = &cur
		users = users[:limit]
	}

	// ---------- response ----------
	c.JSON(http.StatusOK, gin.H{
		"data":        users,
		"next_cursor": nextCursor,
	})
}
