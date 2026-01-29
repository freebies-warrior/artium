package database

import (
	"errors"

	"github.com/jackc/pgx/v5/pgconn"
)

func PgError(err error) (*pgconn.PgError, bool) {
	var pgErr *pgconn.PgError
	if errors.As(err, &pgErr) {
		return pgErr, true
	}
	return nil, false
}
