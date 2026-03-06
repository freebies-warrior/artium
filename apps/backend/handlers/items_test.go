package handlers

import (
	"net/http"
	"testing"

	"backend/middlewares"

	"github.com/gin-gonic/gin"
)

func TestItemsPostItemMissingUserContext(t *testing.T) {
	h := NewItemsHandler(nil, nil, nil, nil, "")
	c, w := newJSONContext(http.MethodPost, "/items", `{"title":"Test","base_price":0,"increment":1,"time_start":"2024-01-02T15:04:05Z","time_end":"2024-01-02T16:04:05Z","picture_keys":["pic"]}`)

	h.PostItem(c)

	assertStatusAndErrorCode(t, w, http.StatusUnauthorized, "UNAUTHORIZED")
}

func TestItemsPostItemInvalidTimes(t *testing.T) {
	h := NewItemsHandler(nil, nil, nil, nil, "")
	c, w := newJSONContext(http.MethodPost, "/items", `{"title":"Test","base_price":0,"increment":1,"time_start":"2024-01-02T15:04:05Z","time_end":"2024-01-02T14:04:05Z","picture_keys":["pic"]}`)
	c.Set(middlewares.CtxUserIDKey, "00000000-0000-0000-0000-000000000001")

	h.PostItem(c)

	assertStatusAndErrorCode(t, w, http.StatusBadRequest, "VALIDATION_ERROR")
}

func TestItemsGetItemMissingID(t *testing.T) {
	h := NewItemsHandler(nil, nil, nil, nil, "")
	c, w := newJSONContext(http.MethodGet, "/items/", "")
	c.Params = gin.Params{{Key: "item_id", Value: ""}}

	h.GetItem(c)

	assertStatusAndErrorCode(t, w, http.StatusBadRequest, "VALIDATION_ERROR")
}

func TestItemsGetItemInvalidID(t *testing.T) {
	h := NewItemsHandler(nil, nil, nil, nil, "")
	c, w := newJSONContext(http.MethodGet, "/items/not-a-uuid", "")
	c.Params = gin.Params{{Key: "item_id", Value: "not-a-uuid"}}

	h.GetItem(c)

	assertStatusAndErrorCode(t, w, http.StatusBadRequest, "VALIDATION_ERROR")
}

func TestItemsListItemsInvalidStatus(t *testing.T) {
	h := NewItemsHandler(nil, nil, nil, nil, "")
	c, w := newJSONContext(http.MethodGet, "/items?status=bad", "")
	c.Request.URL.RawQuery = "status=bad"

	h.ListItems(c)

	assertStatusAndErrorCode(t, w, http.StatusBadRequest, "VALIDATION_ERROR")
}

func TestItemsListItemsInvalidSellerID(t *testing.T) {
	h := NewItemsHandler(nil, nil, nil, nil, "")
	c, w := newJSONContext(http.MethodGet, "/items?seller_id=bad", "")
	c.Request.URL.RawQuery = "seller_id=bad"

	h.ListItems(c)

	assertStatusAndErrorCode(t, w, http.StatusBadRequest, "VALIDATION_ERROR")
}

func TestItemsPutItemFeaturesInvalidID(t *testing.T) {
	h := NewItemsHandler(nil, nil, nil, nil, "")
	c, w := newJSONContext(http.MethodPut, "/items/not-a-uuid/features", `{"features":{"color":"blue"}}`)
	c.Params = gin.Params{{Key: "item_id", Value: "not-a-uuid"}}

	h.PutItemFeatures(c)

	assertStatusAndErrorCode(t, w, http.StatusBadRequest, "VALIDATION_ERROR")
}
