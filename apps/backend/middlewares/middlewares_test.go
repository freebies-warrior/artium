package middlewares

import (
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"backend/utils"

	"github.com/gin-gonic/gin"
)

func init() {
	gin.SetMode(gin.TestMode)
}

func TestRequireAuthMissingBearer(t *testing.T) {
	r := gin.New()
	r.Use(RequireAuth([]byte("secret")))
	r.GET("/protected", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"ok": true})
	})

	w := httptest.NewRecorder()
	req := httptest.NewRequest(http.MethodGet, "/protected", nil)
	r.ServeHTTP(w, req)

	if w.Code != http.StatusUnauthorized {
		t.Fatalf("expected status %d got %d", http.StatusUnauthorized, w.Code)
	}
}

func TestRequireAuthInvalidToken(t *testing.T) {
	r := gin.New()
	r.Use(RequireAuth([]byte("secret")))
	r.GET("/protected", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"ok": true})
	})

	w := httptest.NewRecorder()
	req := httptest.NewRequest(http.MethodGet, "/protected", nil)
	req.Header.Set("Authorization", "Bearer bad-token")
	r.ServeHTTP(w, req)

	if w.Code != http.StatusUnauthorized {
		t.Fatalf("expected status %d got %d", http.StatusUnauthorized, w.Code)
	}
}

func TestRequireAuthSuccess(t *testing.T) {
	secret := []byte("secret")
	token, err := utils.SignJWT(secret, "user-1", "user@example.com", time.Minute)
	if err != nil {
		t.Fatalf("SignJWT error: %v", err)
	}

	r := gin.New()
	r.Use(RequireAuth(secret))
	r.GET("/protected", func(c *gin.Context) {
		uid, _ := c.Get(CtxUserIDKey)
		email, _ := c.Get(CtxEmailKey)
		c.JSON(http.StatusOK, gin.H{"uid": uid, "email": email})
	})

	w := httptest.NewRecorder()
	req := httptest.NewRequest(http.MethodGet, "/protected", nil)
	req.Header.Set("Authorization", "Bearer "+token)
	r.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("expected status %d got %d", http.StatusOK, w.Code)
	}
}

func TestCORSAllowedOrigin(t *testing.T) {
	r := gin.New()
	r.Use(CORS([]string{"https://example.com"}))
	r.GET("/cors", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"ok": true})
	})

	w := httptest.NewRecorder()
	req := httptest.NewRequest(http.MethodGet, "/cors", nil)
	req.Header.Set("Origin", "https://example.com")
	r.ServeHTTP(w, req)

	if w.Header().Get("Access-Control-Allow-Origin") != "https://example.com" {
		t.Fatalf("expected allow origin header to be set")
	}
	if w.Code != http.StatusOK {
		t.Fatalf("expected status %d got %d", http.StatusOK, w.Code)
	}
}

func TestCORSOptionsPreflight(t *testing.T) {
	r := gin.New()
	r.Use(CORS([]string{"https://example.com"}))
	r.GET("/cors", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"ok": true})
	})

	w := httptest.NewRecorder()
	req := httptest.NewRequest(http.MethodOptions, "/cors", nil)
	req.Header.Set("Origin", "https://example.com")
	r.ServeHTTP(w, req)

	if w.Code != http.StatusNoContent {
		t.Fatalf("expected status %d got %d", http.StatusNoContent, w.Code)
	}
}
