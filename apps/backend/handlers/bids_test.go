package handlers

import (
	"net/http"
	"testing"

	"backend/middlewares"

	"github.com/gin-gonic/gin"
)

func TestBidsPlaceBidMissingItemID(t *testing.T) {
	h := NewBidsHandler(nil, nil)
	c, w := newJSONContext(http.MethodPost, "/items//bids", `{"price":10}`)
	c.Params = gin.Params{{Key: "item_id", Value: ""}}

	h.PlaceBid(c)

	assertStatusAndErrorCode(t, w, http.StatusBadRequest, "VALIDATION_ERROR")
}

func TestBidsPlaceBidInvalidPrice(t *testing.T) {
	h := NewBidsHandler(nil, nil)
	c, w := newJSONContext(http.MethodPost, "/items/item/bids", `{"price":0}`)
	c.Params = gin.Params{{Key: "item_id", Value: "item"}}

	h.PlaceBid(c)

	assertStatusAndErrorCode(t, w, http.StatusBadRequest, "VALIDATION_ERROR")
}

func TestBidsPlaceBidMissingAuth(t *testing.T) {
	h := NewBidsHandler(nil, nil)
	c, w := newJSONContext(http.MethodPost, "/items/item/bids", `{"price":10}`)
	c.Params = gin.Params{{Key: "item_id", Value: "item"}}

	h.PlaceBid(c)

	assertStatusAndErrorCode(t, w, http.StatusUnauthorized, "UNAUTHORIZED")
}

func TestBidsPlaceBidEmptyAuth(t *testing.T) {
	h := NewBidsHandler(nil, nil)
	c, w := newJSONContext(http.MethodPost, "/items/item/bids", `{"price":10}`)
	c.Params = gin.Params{{Key: "item_id", Value: "item"}}
	c.Set(middlewares.CtxUserIDKey, "")

	h.PlaceBid(c)

	assertStatusAndErrorCode(t, w, http.StatusUnauthorized, "UNAUTHORIZED")
}

func TestBidsListBidsMissingItemID(t *testing.T) {
	h := NewBidsHandler(nil, nil)
	c, w := newJSONContext(http.MethodGet, "/items//bids", "")
	c.Params = gin.Params{{Key: "item_id", Value: ""}}

	h.ListBids(c)

	assertStatusAndErrorCode(t, w, http.StatusBadRequest, "VALIDATION_ERROR")
}
