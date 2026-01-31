package handlers

import (
	"net/http"
	"strings"

	"backend/database"
	"backend/middlewares"
	"backend/utils"

	"github.com/gin-gonic/gin"
)

type BidsHandler struct {
	bids  *database.BidDatabase
	items *database.ItemDatabase
}

func NewBidsHandler(bids *database.BidDatabase, items *database.ItemDatabase) *BidsHandler {
	return &BidsHandler{bids: bids, items: items}
}

type placeBidReq struct {
	Price int64 `json:"price"`
}

type bidListResp struct {
	Bids []database.Bid `json:"bids"`
}

type bidResp struct {
	Bid database.Bid `json:"bid"`
}

func (h *BidsHandler) PlaceBid(c *gin.Context) {
	itemID := strings.TrimSpace(c.Param("item_id"))
	if itemID == "" {
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "item_id required", map[string]any{"field": "item_id"}))
		return
	}

	var req placeBidReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "invalid json", nil))
		return
	}
	if req.Price <= 0 {
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "price must be positive", map[string]any{"field": "price"}))
		return
	}

	userIDAny, ok := c.Get(middlewares.CtxUserIDKey)
	if !ok {
		c.JSON(http.StatusUnauthorized, utils.NewError("UNAUTHORIZED", "missing auth", nil))
		return
	}
	userID, _ := userIDAny.(string)
	if userID == "" {
		c.JSON(http.StatusUnauthorized, utils.NewError("UNAUTHORIZED", "missing auth", nil))
		return
	}

	if err := h.items.UpdateItemStatus(c.Request.Context(), itemID); err != nil {
		c.JSON(http.StatusInternalServerError, utils.NewError("INTERNAL_ERROR", "failed to update item status", nil))
		return
	}

	bid, err := h.bids.CreateBid(c.Request.Context(), userID, itemID, req.Price)
	if err != nil {
		if pgErr, ok := database.PgError(err); ok {
			if pgErr.Code == "P0001" {
				switch {
				case strings.Contains(pgErr.Message, "Item not found"):
					c.JSON(http.StatusNotFound, utils.NewError("NOT_FOUND", "item not found", nil))
					return
				case strings.Contains(pgErr.Message, "Bid must be positive"):
					c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "price must be positive", map[string]any{"field": "price"}))
					return
				case strings.Contains(pgErr.Message, "Bid too low"):
					c.JSON(http.StatusConflict, utils.NewError("CONFLICT", pgErr.Message, map[string]any{"field": "price"}))
					return
				default:
					c.JSON(http.StatusConflict, utils.NewError("CONFLICT", pgErr.Message, nil))
					return
				}
			}
		}
		c.JSON(http.StatusInternalServerError, utils.NewError("INTERNAL_ERROR", "database error", nil))
		return
	}

	c.JSON(http.StatusCreated, bidResp{Bid: bid})
}

func (h *BidsHandler) ListBids(c *gin.Context) {
	itemID := strings.TrimSpace(c.Param("item_id"))
	if itemID == "" {
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "item_id required", map[string]any{"field": "item_id"}))
		return
	}

	exists, err := h.items.Exists(c.Request.Context(), itemID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, utils.NewError("INTERNAL_ERROR", "database error", nil))
		return
	}
	if !exists {
		c.JSON(http.StatusNotFound, utils.NewError("NOT_FOUND", "item not found", nil))
		return
	}

	bids, err := h.bids.ListBidsForItem(c.Request.Context(), itemID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, utils.NewError("INTERNAL_ERROR", "database error", nil))
		return
	}

	c.JSON(http.StatusOK, bidListResp{Bids: bids})
}
