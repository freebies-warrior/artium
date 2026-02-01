package handlers

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"net/http"
	"path/filepath"
	"strings"
	"time"

	"backend/middlewares"
	"backend/utils"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/service/s3"
	"github.com/gin-gonic/gin"
)

type UploadHandler struct {
	bucket    string
	presigner *s3.PresignClient
}

type presignReq struct {
	Filename    string `json:"filename"`
	ContentType string `json:"content_type"`
}

type presignPutResp struct {
	Key       string `json:"key"`
	UploadURL string `json:"upload_url"`
	ViewURL   string `json:"view_url,omitempty"`
}

func NewUploadHandler(bucket string, s3Client *s3.Client) *UploadHandler {
	return &UploadHandler{
		bucket:    bucket,
		presigner: s3.NewPresignClient(s3Client),
	}
}

func (h *UploadHandler) PresignGetURL(ctx context.Context, key string, expires time.Duration) (string, error) {
	if strings.HasPrefix(key, "http://") || strings.HasPrefix(key, "https://") {
		return key, nil
	}

	out, err := h.presigner.PresignGetObject(
		ctx,
		&s3.GetObjectInput{
			Bucket: aws.String(h.bucket),
			Key:    aws.String(key),
		},
		func(o *s3.PresignOptions) {
			o.Expires = expires
		},
	)
	if err != nil {
		return "", err
	}
	return out.URL, nil
}

func (h *UploadHandler) PresignPutURL(ctx context.Context, key string, contentType string, expires time.Duration) (string, error) {
	if strings.HasPrefix(key, "http://") || strings.HasPrefix(key, "https://") {
		return key, nil
	}

	input := &s3.PutObjectInput{
		Bucket: aws.String(h.bucket),
		Key:    aws.String(key),
	}
	if contentType != "" {
		input.ContentType = aws.String(contentType)
	}

	out, err := h.presigner.PresignPutObject(
		ctx,
		input,
		func(o *s3.PresignOptions) {
			o.Expires = expires
		},
	)
	if err != nil {
		return "", err
	}
	return out.URL, nil
}

func (h *UploadHandler) PresignPut(c *gin.Context) {
	var req presignReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "invalid json", nil))
		return
	}

	ct := strings.TrimSpace(req.ContentType)
	if !strings.HasPrefix(ct, "image/") {
		c.JSON(http.StatusBadRequest, utils.NewError("VALIDATION_ERROR", "only image uploads allowed", map[string]any{"field": "content_type"}))
		return
	}

	filename := strings.TrimSpace(req.Filename)
	if filename == "" {
		filename = "upload"
	}

	uid := c.GetString(middlewares.CtxUserIDKey)
	if uid == "" {
		uid = "anonymous"
	}

	ext := strings.ToLower(filepath.Ext(filename))
	if ext == "" {
		switch ct {
		case "image/jpeg":
			ext = ".jpg"
		case "image/png":
			ext = ".png"
		case "image/webp":
			ext = ".webp"
		}
	}

	key := "uploads/" + uid + "/" + time.Now().UTC().Format("20060102T150405Z") + "-" + randHex(16) + ext

	putOut, err := h.presigner.PresignPutObject(
		c.Request.Context(),
		&s3.PutObjectInput{
			Bucket:      aws.String(h.bucket),
			Key:         aws.String(key),
			ContentType: aws.String(ct),
		},
		func(o *s3.PresignOptions) {
			o.Expires = 72 * time.Hour
		},
	)
	if err != nil {
		c.JSON(http.StatusInternalServerError, utils.NewError("INTERNAL_ERROR", "failed to presign upload url", nil))
		return
	}

	getOut, err := h.presigner.PresignGetObject(
		c.Request.Context(),
		&s3.GetObjectInput{
			Bucket: aws.String(h.bucket),
			Key:    aws.String(key),
		},
		func(o *s3.PresignOptions) {
			o.Expires = 72 * time.Hour
		},
	)
	if err != nil {
		c.JSON(http.StatusInternalServerError, utils.NewError("INTERNAL_ERROR", "failed to presign view url", nil))
		return
	}

	c.JSON(http.StatusOK, presignPutResp{
		Key:       key,
		UploadURL: putOut.URL,
		ViewURL:   getOut.URL,
	})
}

func randHex(nBytes int) string {
	b := make([]byte, nBytes)
	_, _ = rand.Read(b)
	return hex.EncodeToString(b)
}
