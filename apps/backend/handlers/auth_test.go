package handlers

import (
	"net/http"
	"testing"
)

func TestAuthSignupInvalidEmail(t *testing.T) {
	h := NewAuthHandler(nil, nil, nil, []byte("secret"), "http://example.com")
	c, w := newJSONContext(http.MethodPost, "/signup", `{"email":"bad","username":"user","password":"password123"}`)

	h.Signup(c)

	assertStatusAndErrorCode(t, w, http.StatusBadRequest, "VALIDATION_ERROR")
}

func TestAuthLoginMissingCredentials(t *testing.T) {
	h := NewAuthHandler(nil, nil, nil, []byte("secret"), "http://example.com")
	c, w := newJSONContext(http.MethodPost, "/login", `{"email":"","password":""}`)

	h.Login(c)

	assertStatusAndErrorCode(t, w, http.StatusBadRequest, "VALIDATION_ERROR")
}

func TestAuthVerifyEmailMissingToken(t *testing.T) {
	h := NewAuthHandler(nil, nil, nil, []byte("secret"), "http://example.com")
	c, w := newJSONContext(http.MethodPost, "/verify", `{"token":""}`)

	h.VerifyEmail(c)

	assertStatusAndErrorCode(t, w, http.StatusBadRequest, "VALIDATION_ERROR")
}

func TestAuthResendInvalidEmail(t *testing.T) {
	h := NewAuthHandler(nil, nil, nil, []byte("secret"), "http://example.com")
	c, w := newJSONContext(http.MethodPost, "/resend", `{"email":"bad"}`)

	h.ResendVerification(c)

	assertStatusAndErrorCode(t, w, http.StatusBadRequest, "VALIDATION_ERROR")
}
