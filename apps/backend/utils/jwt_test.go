package utils

import (
	"testing"
	"time"
)

func TestSignAndVerifyJWT(t *testing.T) {
	secret := []byte("secret")
	uid := "user-123"
	email := "test@example.com"

	token, err := SignJWT(secret, uid, email, time.Minute)
	if err != nil {
		t.Fatalf("SignJWT error: %v", err)
	}

	claims, err := VerifyJWT(secret, token)
	if err != nil {
		t.Fatalf("VerifyJWT error: %v", err)
	}

	if claims.UID != uid {
		t.Fatalf("UID mismatch: got %q want %q", claims.UID, uid)
	}
	if claims.Email != email {
		t.Fatalf("Email mismatch: got %q want %q", claims.Email, email)
	}
}

func TestVerifyJWTWithWrongSecret(t *testing.T) {
	secret := []byte("secret")
	wrongSecret := []byte("wrong")

	token, err := SignJWT(secret, "uid", "email", time.Minute)
	if err != nil {
		t.Fatalf("SignJWT error: %v", err)
	}

	if _, err := VerifyJWT(wrongSecret, token); err == nil {
		t.Fatalf("expected error when verifying with wrong secret")
	}
}
