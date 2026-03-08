package database

import (
	"errors"
	"strings"

	"github.com/jackc/pgx/v5/pgconn"
)

func PgError(err error) (*pgconn.PgError, bool) {
	var pgErr *pgconn.PgError
	if errors.As(err, &pgErr) {
		return pgErr, true
	}
	return nil, false
}

func IsInvalidUUIDError(err error) bool {
	pgErr, ok := PgError(err)
	if !ok {
		return false
	}
	return pgErr.Code == "22P02" && strings.Contains(strings.ToLower(pgErr.Message), "uuid")
}
