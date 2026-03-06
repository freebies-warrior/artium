package handlers

import (
	"net/http"
	"testing"

	"github.com/gin-gonic/gin"
)

func TestVisualizationsCreateInvalidItemID(t *testing.T) {
	h := NewVisualizationsHandler(nil, nil, nil)
	c, w := newJSONContext(http.MethodPost, "/visualizations", `{"item_id":"not-a-uuid","item_image_key":"item.jpg","room_image_key":"room.jpg"}`)

	h.Create(c)

	assertStatusAndErrorCode(t, w, http.StatusBadRequest, "VALIDATION_ERROR")
}

func TestVisualizationsGetInvalidJobID(t *testing.T) {
	h := NewVisualizationsHandler(nil, nil, nil)
	c, w := newJSONContext(http.MethodGet, "/visualizations/not-a-uuid", "")
	c.Params = gin.Params{{Key: "job_id", Value: "not-a-uuid"}}

	h.Get(c)

	assertStatusAndErrorCode(t, w, http.StatusBadRequest, "VALIDATION_ERROR")
}

func TestVisualizationsUpdateInvalidJobID(t *testing.T) {
	h := NewVisualizationsHandler(nil, nil, nil)
	c, w := newJSONContext(http.MethodPut, "/visualizations/not-a-uuid", `{"status":"queued"}`)
	c.Params = gin.Params{{Key: "job_id", Value: "not-a-uuid"}}

	h.UpdateInternal(c)

	assertStatusAndErrorCode(t, w, http.StatusBadRequest, "VALIDATION_ERROR")
}
