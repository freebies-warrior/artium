package database

import (
	"context"
	"database/sql"
	"errors"
	"time"
)

var ErrInvalidOrExpiredToken = errors.New("invalid_or_expired_token")

type EmailVerificationTokenDatabase struct {
	db *sql.DB
}

func NewEmailVerificationTokenDatabase(db *sql.DB) *EmailVerificationTokenDatabase {
	return &EmailVerificationTokenDatabase{db: db}
}

func (r *EmailVerificationTokenDatabase) CreateToken(ctx context.Context, userID string, tokenHash []byte, expiresAt time.Time) error {
	_, err := r.db.ExecContext(ctx,
		`INSERT INTO email_verification_tokens (user_id, token_hash, expires_at)
		 VALUES ($1, $2, $3)`,
		userID, tokenHash, expiresAt,
	)
	return err
}

func (r *EmailVerificationTokenDatabase) InvalidateUnusedTokens(ctx context.Context, userID string) error {
	_, err := r.db.ExecContext(ctx,
		`UPDATE email_verification_tokens
		 SET used_at = now()
		 WHERE user_id = $1 AND used_at IS NULL`,
		userID,
	)
	return err
}

func (r *EmailVerificationTokenDatabase) VerifyToken(ctx context.Context, tokenHash []byte) (UserPublic, error) {
	tx, err := r.db.BeginTx(ctx, nil)
	if err != nil {
		return UserPublic{}, err
	}
	defer func() { _ = tx.Rollback() }()

	var (
		tokenID string
		userID  string
	)

	// Lock the token row so it can’t be double-used under race.
	err = tx.QueryRowContext(ctx,
		`SELECT id::text, user_id::text
		 FROM email_verification_tokens
		 WHERE token_hash = $1
		 	AND used_at IS NULL
			AND expires_at > now()
		 FOR UPDATE`,
		tokenHash,
	).Scan(&tokenID, &userID)

	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return UserPublic{}, ErrInvalidOrExpiredToken
		}
		return UserPublic{}, err
	}

	// Mark token as used
	if _, err := tx.ExecContext(ctx,
		`UPDATE email_verification_tokens
		 SET used_at = now()
		 WHERE id::uuid = $1`,
		tokenID,
	); err != nil {
		return UserPublic{}, err
	}

	// Mark user verified
	var u UserPublic
	err = tx.QueryRowContext(ctx,
		`UPDATE users
		SET verified = true
		WHERE id = $1
		RETURNING id::text, email, username, verified`,
		userID,
	).Scan(&u.ID, &u.Email, &u.Username, &u.Verified)
	if err != nil {
		return UserPublic{}, err
	}

	if err := tx.Commit(); err != nil {
		return UserPublic{}, err
	}
	return u, nil
}
