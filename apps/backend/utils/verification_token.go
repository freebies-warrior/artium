package utils

import (
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
)

func GenerateVerificationToken() (string, []byte, error) {
	b := make([]byte, 32) // 256-bit random
	if _, err := rand.Read(b); err != nil {
		return "", nil, err
	}
	raw := base64.RawURLEncoding.EncodeToString(b) // URL-safe, no padding

	sum := sha256.Sum256([]byte(raw))
	hash := sum[:]

	return raw, hash, nil
}

func HashVerificationToken(raw string) []byte {
	sum := sha256.Sum256([]byte(raw))
	return sum[:]
}
