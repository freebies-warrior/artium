package handlers

import (
	"net/http"
	"regexp"
	"strconv"
	"strings"
	"time"

	"backend/database"
	"backend/middlewares"
	"backend/utils"

	"github.com/gin-gonic/gin"
)

type ItemsHandler struct {
	items    *database.ItemDatabase
	pictures *database.PictureDatabase
}

func NewItemsHandler(items *database.ItemDatabase, pictures *database.PictureDatabase) *ItemsHandler {
	return &ItemsHandler{items: items, pictures: pictures}
}

type postItemReq struct {
	Title       string   `json:"title"`
	Description *string  `json:"description"`
	Author      *string  `json:"author"`
	BasePrice   int64    `json:"base_price"`
	Increment   int64    `json:"increment"`
	YearCreated *int     `json:"year_created"`
	Height      *float64 `json:"height"`
	Width       *float64 `json:"width"`
	TimeStart   string   `json:"time_start"`
	TimeEnd     string   `json:"time_end"`
	PictureKeys []string `json:"picture_keys"`
}

type postItemResp struct {
	Item database.Item `json:"item"`
}

type getItemResp struct {
	Item database.Item `json:"item"`
}

type listItemsResp struct {
	Items      []database.Item `json:"items"`
	NextCursor *string         `json:"next_cursor"`
}

var uuidPattern = regexp.MustCompile(`^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$`)

func (h *ItemsHandler) PostItem(c *gin.Context) {
	uidAny, ok := c.Get(middlewares.CtxUserIDKey)
	if !ok {
		c.JSON(http.StatusUnauthorized, utils.NewError("UNAUTHORIZED", "missing user context", nil))
		return
	}
	sellerID, _ := uidAny.(string)
	if strings.TrimSpace(sellerID) == "" {
		c.JSON(http.StatusUnauthorized, utils.NewError("UNAUTHORIZED", "invalid user context", nil))
		return
	}

	var req postItemReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "invalid json", nil))
		return
	}

	title := strings.TrimSpace(req.Title)
	if title == "" {
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "title required", map[string]any{"field": "title"}))
		return
	}
	if req.Increment <= 0 {
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "increment must be > 0", map[string]any{"field": "increment"}))
		return
	}
	if req.BasePrice < 0 {
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "base_price must be >= 0", map[string]any{"field": "base_price"}))
		return
	}

	ts, err := time.Parse(time.RFC3339, req.TimeStart)
	if err != nil {
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "invalid time_start (RFC3339)", map[string]any{"field": "time_start"}))
		return
	}
	te, err := time.Parse(time.RFC3339, req.TimeEnd)
	if err != nil {
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "invalid time_end (RFC3339)", map[string]any{"field": "time_end"}))
		return
	}
	if !te.After(ts) {
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "time_end must be after time_start", nil))
		return
	}

	// optional: require at least 1 picture
	if len(req.PictureKeys) == 0 {
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "at least one picture_keys is required", map[string]any{"field": "picture_keys"}))
		return
	}

	it, err := h.items.CreateItem(c.Request.Context(), database.CreateItemArgs{
		SellerID:    sellerID,
		Title:       title,
		Description: req.Description,
		Author:      req.Author,
		BasePrice:   req.BasePrice,
		Increment:   req.Increment,
		YearCreated: req.YearCreated,
		Height:      req.Height,
		Width:       req.Width,
		TimeStart:   ts,
		TimeEnd:     te,
	})
	if err != nil {
		c.JSON(http.StatusInternalServerError, utils.NewError("INTERNAL_ERROR", "database error", nil))
		return
	}

	pics, err := h.pictures.CreatePictures(c.Request.Context(), it.ID, req.PictureKeys)
	if err != nil {
		c.JSON(http.StatusInternalServerError, utils.NewError("INTERNAL_ERROR", "failed to create pictures", nil))
		return
	}

	it.Pictures = pics
	c.JSON(http.StatusCreated, postItemResp{Item: it})
}

func (h *ItemsHandler) GetItem(c *gin.Context) {
	itemID := c.Param("item_id")
	if strings.TrimSpace(itemID) == "" {
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "item_id required", nil))
		return
	}

	it, err := h.items.GetItemByID(c.Request.Context(), itemID)
	if err != nil {
		if err == database.ErrNotFound {
			c.JSON(http.StatusNotFound, utils.NewError("NOT_FOUND", "item not found", nil))
			return
		}
		c.JSON(http.StatusInternalServerError, utils.NewError("INTERNAL_ERROR", "database error", nil))
		return
	}

	pics, err := h.pictures.GetPicturesByItemID(c.Request.Context(), it.ID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, utils.NewError("INTERNAL_ERROR", "failed to fetch pictures", nil))
		return
	}
	it.Pictures = pics

	c.JSON(http.StatusOK, getItemResp{Item: it})
}

func (h *ItemsHandler) ListItems(c *gin.Context) {
	limit := 20
	if s := strings.TrimSpace(c.Query("limit")); s != "" {
		n, err := strconv.Atoi(s)
		if err != nil {
			c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "invalid limit", map[string]any{"field": "limit"}))
			return
		}
		limit = n
	}

	status := strings.TrimSpace(c.Query("status"))
	if status != "" {
		switch strings.ToLower(status) {
		case "draft", "active", "ended", "cancelled":
		default:
			c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "invalid status", map[string]any{"field": "status"}))
			return
		}
	}

	sellerID := strings.TrimSpace(c.Query("seller_id"))
	if sellerID != "" {
		if !uuidPattern.MatchString(sellerID) {
			c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "invalid seller_id", map[string]any{"field": "seller_id"}))
			return
		}
	}

	q := strings.TrimSpace(c.Query("q"))
	cursor := strings.TrimSpace(c.Query("cursor"))

	items, next, err := h.items.ListItems(c.Request.Context(), database.ListItemsParams{
		Limit:    limit,
		Cursor:   cursor,
		Status:   status,
		SellerID: sellerID,
		Query:    q,
	})
	if err != nil {
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "invalid query params", nil))
		return
	}

	// attach 1 picture per item for list view
	ids := make([]string, 0, len(items))
	for i := range items {
		ids = append(ids, items[i].ID)
	}
	firstPics, err := h.pictures.GetFirstPicturesByItemIDs(c.Request.Context(), ids)
	if err != nil {
		c.JSON(http.StatusInternalServerError, utils.NewError("INTERNAL_ERROR", "failed to fetch pictures", nil))
		return
	}
	for i := range items {
		if p, ok := firstPics[items[i].ID]; ok {
			items[i].Pictures = []database.PicturePublic{p}
		} else {
			items[i].Pictures = []database.PicturePublic{}
		}
	}

	c.JSON(http.StatusOK, listItemsResp{
		Items:      items,
		NextCursor: next,
	})
}
