package utils

import (
	"bytes"
	"testing"
)

func TestGenerateVerificationToken(t *testing.T) {
	raw, hash, err := GenerateVerificationToken()
	if err != nil {
		t.Fatalf("GenerateVerificationToken error: %v", err)
	}
	if raw == "" {
		t.Fatalf("expected raw token to be non-empty")
	}
	if len(hash) != 32 {
		t.Fatalf("expected hash length 32 got %d", len(hash))
	}

	recomputed := HashVerificationToken(raw)
	if !bytes.Equal(hash, recomputed) {
		t.Fatalf("expected hash to match recomputed hash")
	}
}
