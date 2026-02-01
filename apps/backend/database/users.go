package database

import (
	"context"
	"database/sql"
	"encoding/base64"
	"errors"
	"strings"
	"time"

	"github.com/jackc/pgx/v5/pgconn"
)

type UserDatabase struct {
	db *sql.DB
}

func NewUserDatabase(db *sql.DB) *UserDatabase {
	return &UserDatabase{db: db}
}

type UserPublic struct {
	ID       string `json:"id"`
	Email    string `json:"email"`
	Username string `json:"username"`
	Verified bool   `json:"verified"`
}

type UserRow struct {
	ID           string
	Email        string
	Username     string
	Verified     bool
	PasswordHash string
}

type PublicUserDetails struct {
	ID        string    `json:"id"`
	Username  string    `json:"username"`
	CreatedAt time.Time `json:"created_at"`
}


type ListUsersParams struct {
	Limit  int
	Cursor string
	Query  string
}

func (r *UserDatabase) CreateUser(ctx context.Context, email, username, passwordHash string) (UserPublic, error) {
	var u UserPublic
	err := r.db.QueryRowContext(ctx,
		`INSERT INTO users (email, username, password_hash, verified)
		 VALUES ($1, $2, $3, false)
		 RETURNING id::text, email, username, verified`,
		email, username, passwordHash,
	).Scan(&u.ID, &u.Email, &u.Username, &u.Verified)
	return u, err
}

func (r *UserDatabase) GetUserByEmail(ctx context.Context, email string) (UserRow, error) {
	var u UserRow
	err := r.db.QueryRowContext(ctx,
		`SELECT id::text, email, username, verified, password_hash
		 FROM users
		 WHERE email = $1`,
		email,
	).Scan(&u.ID, &u.Email, &u.Username, &u.Verified, &u.PasswordHash)
	return u, err
}

func (r *UserDatabase) GetUserDetailsByUserID(
	ctx context.Context,
	userID string,
) (UserPublic, error) {
	var u UserPublic
	err := r.db.QueryRowContext(ctx,
		`SELECT id::text, email, username, verified
		 FROM users
		 WHERE id = $1`,
		userID,
	).Scan(&u.ID, &u.Email, &u.Username, &u.Verified)
	return u, err
}


func IsUniqueViolation(err error) bool {
	var pgErr *pgconn.PgError
	if errors.As(err, &pgErr) {
		return pgErr.Code == "23505" // unique_violation
	}
	return false
}

// To know which violates the uniqueness (e.g. email or username)
func UniqueViolationConstraint(err error) (string, bool) {
	var pgErr *pgconn.PgError
	if errors.As(err, &pgErr) && pgErr.Code == "23505" {
		return pgErr.ConstraintName, true
	}
	return "", false
}

func makeUserCursor(createdAt time.Time, id string) string {
	raw := createdAt.UTC().Format(time.RFC3339Nano) + "|" + id
	return base64.RawURLEncoding.EncodeToString([]byte(raw))
}

func parseUserCursor(cur string) (*time.Time, *string, error) {
	b, err := base64.RawURLEncoding.DecodeString(cur)
	if err != nil {
		return nil, nil, err
	}
	parts := strings.SplitN(string(b), "|", 2)
	if len(parts) != 2 {
		return nil, nil, errors.New("bad cursor")
	}
	t, err := time.Parse(time.RFC3339Nano, parts[0])
	if err != nil {
		return nil, nil, err
	}
	id := parts[1]
	return &t, &id, nil
}

func (r *UserDatabase) ListUsers(
	ctx context.Context,
	p ListUsersParams,
) ([]PublicUserDetails, *string, error) {

	limit := p.Limit
	if limit <= 0 {
		limit = 20
	}
	if limit > 100 {
		limit = 100
	}

	q := strings.TrimSpace(p.Query)
	qLike := "%" + q + "%"

	// ----- cursor handling (same pattern as items) -----
	hasCursor := false
	var curT time.Time
	var curID string

	if strings.TrimSpace(p.Cursor) != "" {
		t, id, err := parseUserCursor(p.Cursor)
		if err != nil {
			return nil, nil, err
		}
		hasCursor = true
		curT = *t
		curID = *id
	} else {
		curT = time.Unix(0, 0).UTC()
		curID = "00000000-0000-0000-0000-000000000000"
	}

	rows, err := r.db.QueryContext(ctx, `
		SELECT
			id::text,
			username,
			created_at
		FROM users
		WHERE
			($1 = '' OR username ILIKE $2)
			AND (NOT $3 OR (created_at, id) < ($4, $5::uuid))
		ORDER BY created_at DESC, id DESC
		LIMIT $6
	`, q, qLike, hasCursor, curT, curID, limit+1)
	if err != nil {
		return nil, nil, err
	}
	defer rows.Close()

	users := make([]PublicUserDetails, 0, limit+1)
	for rows.Next() {
		var u PublicUserDetails
		if err := rows.Scan(
			&u.ID,
			&u.Username,
			&u.CreatedAt,
		); err != nil {
			return nil, nil, err
		}
		users = append(users, u)
	}
	if err := rows.Err(); err != nil {
		return nil, nil, err
	}

	// ----- next cursor -----
	var next *string
	if len(users) > limit {
		last := users[limit-1]
		nc := makeUserCursor(last.CreatedAt, last.ID)
		next = &nc
		users = users[:limit]
	}

	return users, next, nil
}
