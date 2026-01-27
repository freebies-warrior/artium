package utils

import (
	"time"

	"github.com/golang-jwt/jwt/v5"
)

type Claims struct {
	UID   string `json:"uid"`
	Email string `json:"email"`
	jwt.RegisteredClaims
}

func SignJWT(secret []byte, uid, email string, ttl time.Duration) (string, error) {
	now := time.Now()
	c := Claims{
		UID:   uid,
		Email: email,
		RegisteredClaims: jwt.RegisteredClaims{
			IssuedAt:  jwt.NewNumericDate(now),
			ExpiresAt: jwt.NewNumericDate(now.Add(ttl)),
		},
	}
	t := jwt.NewWithClaims(jwt.SigningMethodHS256, c)
	return t.SignedString(secret)
}
