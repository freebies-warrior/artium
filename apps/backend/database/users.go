package database

import (
	"context"
	"database/sql"
	"errors"

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
	Verified bool   `json:"verified"`
}

type UserRow struct {
	ID           string
	Email        string
	Verified     bool
	PasswordHash string
}

func (r *UserDatabase) CreateUser(ctx context.Context, email, passwordHash string) (UserPublic, error) {
	var u UserPublic
	err := r.db.QueryRowContext(ctx,
		`INSERT INTO users (email, password_hash, verified)
		 VALUES ($1, $2, false)
		 RETURNING id::text, email, verified`,
		email, passwordHash,
	).Scan(&u.ID, &u.Email, &u.Verified)
	return u, err
}

func (r *UserDatabase) GetUserByEmail(ctx context.Context, email string) (UserRow, error) {
	var u UserRow
	err := r.db.QueryRowContext(ctx,
		`SELECT id::text, email, verified, password_hash
		 FROM users WHERE email = $1`,
		email,
	).Scan(&u.ID, &u.Email, &u.Verified, &u.PasswordHash)
	return u, err
}

func IsUniqueViolation(err error) bool {
	var pgErr *pgconn.PgError
	if errors.As(err, &pgErr) {
		return pgErr.Code == "23505" // unique_violation
	}
	return false
}
