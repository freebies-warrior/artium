package handlers

import (
	"net/http"
	"testing"

	"github.com/gin-gonic/gin"
)

func TestUsersGetUserDetailsMissingID(t *testing.T) {
	h := NewUserHandler(nil)
	c, w := newJSONContext(http.MethodGet, "/users/", "")
	c.Params = gin.Params{{Key: "user_id", Value: ""}}

	h.GetUserDetails(c)

	assertStatusAndErrorCode(t, w, http.StatusBadRequest, "VALIDATION_ERROR")
}

func TestUsersGetUserDetailsInvalidID(t *testing.T) {
	h := NewUserHandler(nil)
	c, w := newJSONContext(http.MethodGet, "/users/not-a-uuid", "")
	c.Params = gin.Params{{Key: "user_id", Value: "not-a-uuid"}}

	h.GetUserDetails(c)

	assertStatusAndErrorCode(t, w, http.StatusBadRequest, "VALIDATION_ERROR")
}
