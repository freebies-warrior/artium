package handlers

import (
	"encoding/hex"
	"errors"
	"net/http"
	"strings"

	"backend/database"
	"backend/utils"

	"github.com/gin-gonic/gin"
)

var errInvalidUUID = errors.New("invalid uuid")

func isUUID(value string) bool {
	_, err := parseUUID(value)
	return err == nil
}

func parseUUID(value string) ([16]byte, error) {
	var out [16]byte

	s := strings.TrimSpace(value)
	if s == "" {
		return out, errInvalidUUID
	}

	if strings.HasPrefix(s, "{") || strings.HasSuffix(s, "}") {
		if len(s) < 2 || s[0] != '{' || s[len(s)-1] != '}' {
			return out, errInvalidUUID
		}
		s = s[1 : len(s)-1]
	}

	hexDigits := make([]byte, 0, 32)
	digitsSinceSeparator := 0
	for i := 0; i < len(s); i++ {
		ch := s[i]
		switch {
		case isHexDigit(ch):
			hexDigits = append(hexDigits, ch)
			digitsSinceSeparator++
			if len(hexDigits) > 32 {
				return out, errInvalidUUID
			}
		case ch == '-':
			if digitsSinceSeparator == 0 || digitsSinceSeparator%4 != 0 {
				return out, errInvalidUUID
			}
			digitsSinceSeparator = 0
		default:
			return out, errInvalidUUID
		}
	}

	if len(hexDigits) != 32 || digitsSinceSeparator == 0 && strings.Contains(s, "-") {
		return out, errInvalidUUID
	}

	buf, err := hex.DecodeString(string(hexDigits))
	if err != nil {
		return out, errInvalidUUID
	}
	copy(out[:], buf)
	return out, nil
}

func isHexDigit(ch byte) bool {
	switch {
	case ch >= '0' && ch <= '9':
		return true
	case ch >= 'a' && ch <= 'f':
		return true
	case ch >= 'A' && ch <= 'F':
		return true
	default:
		return false
	}
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
