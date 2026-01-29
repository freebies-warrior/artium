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
