package handlers

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
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
	uploads  *UploadHandler
	features *FeatureExtractorClient
	baseURL  string
}

func NewItemsHandler(items *database.ItemDatabase, pictures *database.PictureDatabase, uploads *UploadHandler, features *FeatureExtractorClient, baseURL string) *ItemsHandler {
	return &ItemsHandler{
		items:    items,
		pictures: pictures,
		uploads:  uploads,
		features: features,
		baseURL:  strings.TrimRight(baseURL, "/"),
	}
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

func (h *ItemsHandler) presignPictures(ctx context.Context, pics []database.PicturePublic) error {
	for i := range pics {
		signed, err := h.uploads.PresignGetURL(ctx, pics[i].Key, 72*time.Hour)
		if err != nil {
			return err
		}
		pics[i].URL = signed
	}
	return nil
}

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
	if !isUUID(sellerID) {
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

	go func(item database.Item, pictures []database.PicturePublic) {
		ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
		defer cancel()
		if err := h.triggerFeatureExtraction(ctx, item, pictures); err != nil {
			log.Printf("feature extraction enqueue failed for item %s: %v", item.ID, err)
		}
	}(it, pics)

	it.Pictures = pics
	c.JSON(http.StatusCreated, postItemResp{Item: it})
}

func (h *ItemsHandler) GetItem(c *gin.Context) {
	itemID := strings.TrimSpace(c.Param("item_id"))
	if itemID == "" {
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "item_id required", nil))
		return
	}
	if !isUUID(itemID) {
		invalidUUIDResponse(c, "item_id")
		return
	}

	it, err := h.items.GetItemByID(c.Request.Context(), itemID)
	if err != nil {
		if err == database.ErrNotFound {
			c.JSON(http.StatusNotFound, utils.NewError("NOT_FOUND", "item not found", nil))
			return
		}
		if handleInvalidUUIDDBError(c, err, "item_id") {
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
	if err := h.presignPictures(c.Request.Context(), pics); err != nil {
		c.JSON(http.StatusInternalServerError, utils.NewError("INTERNAL_ERROR", "failed to sign image urls", nil))
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
		if !isUUID(sellerID) {
			invalidUUIDResponse(c, "seller_id")
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

	for i := range items {
		if err := h.presignPictures(c.Request.Context(), items[i].Pictures); err != nil {
			c.JSON(http.StatusInternalServerError, utils.NewError("INTERNAL_ERROR", "failed to sign image urls", nil))
			return
		}
	}

	c.JSON(http.StatusOK, listItemsResp{
		Items:      items,
		NextCursor: next,
	})
}

type putItemFeaturesReq struct {
	Features json.RawMessage `json:"features"`
}

func (h *ItemsHandler) PutItemFeatures(c *gin.Context) {
	itemID := strings.TrimSpace(c.Param("item_id"))
	if itemID == "" || !isUUID(itemID) {
		invalidUUIDResponse(c, "item_id")
		return
	}

	var req putItemFeaturesReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "invalid json", nil))
		return
	}

	if len(req.Features) == 0 || string(req.Features) == "null" {
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "features is required", map[string]any{"field": "features"}))
		return
	}

	// Ensure "features" is a JSON object
	var v any
	if err := json.Unmarshal(req.Features, &v); err != nil {
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "features must be valid json", map[string]any{"field": "features"}))
		return
	}
	if _, ok := v.(map[string]any); !ok {
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "features must be a JSON object", map[string]any{"field": "features"}))
		return
	}

	if err := h.items.UpdateItemFeatures(c.Request.Context(), itemID, string(req.Features)); err != nil {
		if err == database.ErrNotFound {
			c.JSON(http.StatusNotFound, utils.NewError("NOT_FOUND", "item not found", nil))
			return
		}
		if handleInvalidUUIDDBError(c, err, "item_id") {
			return
		}
		c.JSON(http.StatusInternalServerError, utils.NewError("INTERNAL_ERROR", "failed to update item features", nil))
		return
	}

	c.JSON(http.StatusOK, gin.H{"ok": true})
}

func (h *ItemsHandler) triggerFeatureExtraction(ctx context.Context, item database.Item, pics []database.PicturePublic) error {
	if h.features == nil {
		return nil
	}

	imageKeys := make([]string, 0, len(pics))
	imageURLs := make([]string, 0, len(pics))
	for i := range pics {
		key := strings.TrimSpace(pics[i].Key)
		if key == "" {
			continue
		}
		signed, err := h.uploads.PresignGetURL(ctx, key, 72*time.Hour)
		if err != nil {
			return err
		}
		imageKeys = append(imageKeys, key)
		imageURLs = append(imageURLs, signed)
	}

	if len(imageKeys) == 0 {
		return nil
	}

	return h.features.Enqueue(ctx, featureExtractionRequest{
		ItemID:       item.ID,
		ImageKeys:    imageKeys,
		ImageGetURLs: imageURLs,
		CallbackURL:  h.baseURL + "/internal/items/" + item.ID + "/features",
		Metadata: featureExtractionMetadata{
			Author:      item.Author,
			Title:       item.Title,
			YearCreated: item.YearCreated,
		},
	})
}
