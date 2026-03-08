package handlers

import (
	"context"
	"database/sql"
	"database/sql/driver"
	"encoding/json"
	"errors"
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

func newErrorDB(err error) *sql.DB {
	return sql.OpenDB(errorConnector{err: err})
}

type errorConnector struct {
	err error
}

func (c errorConnector) Connect(context.Context) (driver.Conn, error) {
	return errorConn{err: c.err}, nil
}

func (c errorConnector) Driver() driver.Driver {
	return errorDriver{}
}

type errorDriver struct{}

func (d errorDriver) Open(string) (driver.Conn, error) {
	return nil, errors.New("not implemented")
}

type errorConn struct {
	err error
}

func (c errorConn) Prepare(string) (driver.Stmt, error) {
	return nil, errors.New("not implemented")
}

func (c errorConn) Close() error {
	return nil
}

func (c errorConn) Begin() (driver.Tx, error) {
	return nil, errors.New("not implemented")
}

func (c errorConn) QueryContext(context.Context, string, []driver.NamedValue) (driver.Rows, error) {
	return nil, c.err
}

func (c errorConn) ExecContext(context.Context, string, []driver.NamedValue) (driver.Result, error) {
	return nil, c.err
}
