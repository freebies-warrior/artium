package handlers

import (
	"encoding/json"
	"net/http/httptest"
	"strings"
	"testing"

	"backend/utils"

	"github.com/gin-gonic/gin"
)

func init() {
	gin.SetMode(gin.TestMode)
}

func newJSONContext(method, path, body string) (*gin.Context, *httptest.ResponseRecorder) {
	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(method, path, strings.NewReader(body))
	c.Request.Header.Set("Content-Type", "application/json")
	return c, w
}

func decodeErrorResponse(t *testing.T, w *httptest.ResponseRecorder) utils.ErrorResponse {
	t.Helper()
	var resp utils.ErrorResponse
	if err := json.NewDecoder(w.Body).Decode(&resp); err != nil {
		t.Fatalf("decode response: %v", err)
	}
	return resp
}

func assertStatus(t *testing.T, w *httptest.ResponseRecorder, want int) {
	t.Helper()
	if w.Code != want {
		t.Fatalf("status mismatch: got %d want %d", w.Code, want)
	}
}

func assertErrorCode(t *testing.T, w *httptest.ResponseRecorder, want string) {
	t.Helper()
	resp := decodeErrorResponse(t, w)
	if resp.Error.Code != want {
		t.Fatalf("error code mismatch: got %q want %q", resp.Error.Code, want)
	}
}

func assertStatusAndErrorCode(t *testing.T, w *httptest.ResponseRecorder, wantStatus int, wantCode string) {
	t.Helper()
	assertStatus(t, w, wantStatus)
	assertErrorCode(t, w, wantCode)
}
