package utils

import "testing"

func TestHashAndCheckPassword(t *testing.T) {
	plain := "super-secret"

	hash, err := HashPassword(plain)
	if err != nil {
		t.Fatalf("HashPassword error: %v", err)
	}
	if hash == plain {
		t.Fatalf("expected hash to differ from plain text")
	}

	if !CheckPassword(hash, plain) {
		t.Fatalf("expected password to validate")
	}
	if CheckPassword(hash, "wrong") {
		t.Fatalf("expected password to fail validation")
	}
}
