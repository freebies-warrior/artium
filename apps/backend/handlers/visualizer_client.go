package handlers

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"
)

type VisualizerClient struct {
	baseURL string
	token   string
	client  *http.Client
}

type visualizeInstallationReq struct {
	RoomURL        string `json:"room_url"`
	ArtURL         string `json:"art_url"`
	UploadImageURL string `json:"upload_image_url"`
	ResultImageKey string `json:"result_image_key"`
	JobID          string `json:"job_id"`
	ItemDimensions *struct {
		Width  float64 `json:"width"`
		Height float64 `json:"height"`
	} `json:"item_dimensions,omitempty"`
}

func NewVisualizerClient(baseURL string, token string) *VisualizerClient {
	return &VisualizerClient{
		baseURL: strings.TrimRight(baseURL, "/"),
		token:   token,
		client: &http.Client{
			Timeout: 10 * time.Second,
		},
	}
}

func (c *VisualizerClient) Enqueue(ctx context.Context, payload visualizeInstallationReq) error {
	url := c.baseURL + "/agents/visualizer/visualize_installation"
	body, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf("marshal payload: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewReader(body))
	if err != nil {
		return fmt.Errorf("build request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")
	if c.token != "" {
		req.Header.Set("X-Internal-Token", c.token)
	}

	resp, err := c.client.Do(req)
	if err != nil {
		return fmt.Errorf("send request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		msg, _ := io.ReadAll(io.LimitReader(resp.Body, 2048))
		return fmt.Errorf("unexpected status %d: %s", resp.StatusCode, strings.TrimSpace(string(msg)))
	}

	return nil
}
