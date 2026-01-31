package handlers

import (
	"net/http"
	"regexp"
	"strings"
	"time"

	"backend/database"
	"backend/middlewares"
	"backend/utils"

	"github.com/gin-gonic/gin"
)

type VisualizationsHandler struct {
	jobs    *database.VisualizationJobDatabase
	uploads *UploadHandler
}

func NewVisualizationsHandler(jobs *database.VisualizationJobDatabase, uploads *UploadHandler) *VisualizationsHandler {
	return &VisualizationsHandler{jobs: jobs, uploads: uploads}
}

type createVisualizationReq struct {
	ItemID       string `json:"item_id"`
	ItemImageKey string `json:"item_image_key"`
	RoomImageKey string `json:"room_image_key"`

	ItemDimensions *struct {
		WidthCM  float64 `json:"width_cm"`
		HeightCM float64 `json:"height_cm"`
	} `json:"item_dimensions,omitempty"`
}

type visualizationJobOut struct {
	ID                string    `json:"id"`
	UserID            string    `json:"user_id"`
	ItemID            string    `json:"item_id"`
	ItemImageKey      string    `json:"item_image_key"`
	RoomImageKey      string    `json:"room_image_key"`
	Status            string    `json:"status"`
	ResultImageKey    *string   `json:"result_image_key,omitempty"`
	ResultImageURL    *string   `json:"result_image_url,omitempty"`
	ResultDescription *string   `json:"result_description,omitempty"`
	ErrorMessage      *string   `json:"error_message,omitempty"`
	CreatedAt         time.Time `json:"created_at"`
	UpdatedAt         time.Time `json:"updated_at"`
}

type jobResp struct {
	Job visualizationJobOut `json:"job"`
}

var uuidRe = regexp.MustCompile(`(?i)^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`)

func (h *VisualizationsHandler) Create(c *gin.Context) {
	var req createVisualizationReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "invalid json", nil))
		return
	}

	itemID := strings.TrimSpace(req.ItemID)
	if !uuidRe.MatchString(itemID) {
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "invalid item_id", map[string]any{"field": "item_id"}))
		return
	}

	itemKey := strings.TrimSpace(req.ItemImageKey)
	if itemKey == "" {
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "item_image_key required", map[string]any{"field": "item_image_key"}))
		return
	}

	roomKey := strings.TrimSpace(req.RoomImageKey)
	if roomKey == "" {
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "room_image_key required", map[string]any{"field": "room_image_key"}))
		return
	}

	uid := c.GetString(middlewares.CtxUserIDKey)
	if uid == "" {
		c.JSON(http.StatusUnauthorized, utils.NewError("UNAUTHORIZED", "missing auth", nil))
		return
	}

	// Ensure item_image_key belongs to the item (and item has images)
	ok, err := h.jobs.ItemHasPictureKey(c.Request.Context(), itemID, itemKey)
	if err != nil {
		c.JSON(http.StatusInternalServerError, utils.NewError("INTERNAL_ERROR", "database error", nil))
		return
	}
	if !ok {
		c.JSON(http.StatusConflict, utils.NewError("CONFLICT", "item has no image matching item_image_key", nil))
		return
	}

	job, err := h.jobs.CreateJob(c.Request.Context(), database.CreateVisualizationJobArgs{
		UserID:       uid,
		ItemID:       itemID,
		ItemImageKey: itemKey,
		RoomImageKey: roomKey,
	})
	if err != nil {
		c.JSON(http.StatusInternalServerError, utils.NewError("INTERNAL_ERROR", "failed to create visualization job", nil))
		return
	}

	c.JSON(http.StatusCreated, jobResp{Job: toJobOut(job, nil)})
}

func (h *VisualizationsHandler) Get(c *gin.Context) {
	jobID := strings.TrimSpace(c.Param("job_id"))
	if !uuidRe.MatchString(jobID) {
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "invalid job_id", map[string]any{"field": "job_id"}))
		return
	}

	uid := c.GetString(middlewares.CtxUserIDKey)
	if uid == "" {
		c.JSON(http.StatusUnauthorized, utils.NewError("UNAUTHORIZED", "missing auth", nil))
		return
	}

	job, err := h.jobs.GetJobByID(c.Request.Context(), jobID)
	if err != nil {
		if err == database.ErrNotFound {
			c.JSON(http.StatusNotFound, utils.NewError("NOT_FOUND", "job not found", nil))
			return
		}
		c.JSON(http.StatusInternalServerError, utils.NewError("INTERNAL_ERROR", "database error", nil))
		return
	}

	if job.UserID != uid {
		c.JSON(http.StatusForbidden, utils.NewError("FORBIDDEN", "not allowed to access this job", nil))
		return
	}

	var signedURL *string
	if job.Status == "succeeded" && job.ResultImageKey != nil && *job.ResultImageKey != "" {
		u, err := h.uploads.PresignGetURL(c.Request.Context(), *job.ResultImageKey, 10*time.Minute)
		if err != nil {
			c.JSON(http.StatusInternalServerError, utils.NewError("INTERNAL_ERROR", "failed to sign result image url", nil))
			return
		}
		signedURL = &u
	}

	c.JSON(http.StatusOK, jobResp{Job: toJobOut(job, signedURL)})
}

type updateVisualizationReq struct {
	Status            string  `json:"status"`
	ResultImageKey    *string `json:"result_image_key"`
	ResultDescription *string `json:"result_description"`
	ErrorMessage      *string `json:"error_message"`
}

func (h *VisualizationsHandler) UpdateInternal(c *gin.Context) {
	jobID := strings.TrimSpace(c.Param("job_id"))
	if !uuidRe.MatchString(jobID) {
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "invalid job_id", map[string]any{"field": "job_id"}))
		return
	}

	var req updateVisualizationReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "invalid json", nil))
		return
	}

	status := strings.TrimSpace(strings.ToLower(req.Status))
	switch status {
	case "queued", "processing", "succeeded", "failed":
	default:
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "invalid status", map[string]any{"field": "status"}))
		return
	}

	// If succeeded, you almost always want a result_image_key.
	if status == "succeeded" {
		if req.ResultImageKey == nil || strings.TrimSpace(*req.ResultImageKey) == "" {
			c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "result_image_key required when succeeded", map[string]any{"field": "result_image_key"}))
			return
		}
	}

	if err := h.jobs.UpdateJobInternal(c.Request.Context(), jobID, database.UpdateVisualizationJobArgs{
		Status:            status,
		ResultImageKey:    req.ResultImageKey,
		ResultDescription: req.ResultDescription,
		ErrorMessage:      req.ErrorMessage,
	}); err != nil {
		if err == database.ErrNotFound {
			c.JSON(http.StatusNotFound, utils.NewError("NOT_FOUND", "job not found", nil))
			return
		}
		c.JSON(http.StatusInternalServerError, utils.NewError("INTERNAL_ERROR", "failed to update job", nil))
		return
	}

	c.JSON(http.StatusOK, gin.H{"ok": true})
}

func toJobOut(job database.VisualizationJob, signedResultURL *string) visualizationJobOut {
	return visualizationJobOut{
		ID:                job.ID,
		UserID:            job.UserID,
		ItemID:            job.ItemID,
		ItemImageKey:      job.ItemImageKey,
		RoomImageKey:      job.RoomImageKey,
		Status:            job.Status,
		ResultImageKey:    job.ResultImageKey,
		ResultImageURL:    signedResultURL,
		ResultDescription: job.ResultDescription,
		ErrorMessage:      job.ErrorMessage,
		CreatedAt:         job.CreatedAt,
		UpdatedAt:         job.UpdatedAt,
	}
}
