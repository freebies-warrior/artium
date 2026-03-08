package database

import (
	"testing"

	"github.com/jackc/pgx/v5/pgconn"
)

func TestIsInvalidUUIDError(t *testing.T) {
	err := &pgconn.PgError{
		Code:    "22P02",
		Message: `invalid input syntax for type uuid: "not-a-uuid"`,
	}

	if !IsInvalidUUIDError(err) {
		t.Fatal("expected invalid uuid error to be detected")
	}
}

func TestIsInvalidUUIDErrorFalseForOtherTextErrors(t *testing.T) {
	err := &pgconn.PgError{
		Code:    "22P02",
		Message: `invalid input syntax for type integer: "abc"`,
	}

	if IsInvalidUUIDError(err) {
		t.Fatal("expected non-uuid text error to be ignored")
	}
}
