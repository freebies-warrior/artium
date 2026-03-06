package handlers

import (
	"net/http"
	"regexp"
	"strings"

	"backend/database"
	"backend/utils"

	"github.com/gin-gonic/gin"
)

var uuidPattern = regexp.MustCompile(`(?i)^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`)

func isUUID(value string) bool {
	return uuidPattern.MatchString(strings.TrimSpace(value))
}

func invalidUUIDResponse(c *gin.Context, field string) {
	message := "invalid uuid"
	var details map[string]any
	if field != "" {
		message = "invalid " + field
		details = map[string]any{"field": field}
	}
	c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", message, details))
}

func handleInvalidUUIDDBError(c *gin.Context, err error, field string) bool {
	if !database.IsInvalidUUIDError(err) {
		return false
	}
	invalidUUIDResponse(c, field)
	return true
}
