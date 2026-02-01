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

type FeatureExtractorClient struct {
	baseURL string
	token   string
	client  *http.Client
}

type featureExtractionMetadata struct {
	Author      *string `json:"author,omitempty"`
	Title       string  `json:"title"`
	YearCreated *int    `json:"year,omitempty"`
}

type featureExtractionRequest struct {
	ItemID       string                    `json:"item_id"`
	ImageKeys    []string                  `json:"image_keys"`
	ImageGetURLs []string                  `json:"image_get_urls"`
	CallbackURL  string                    `json:"callback_url"`
	Metadata     featureExtractionMetadata `json:"metadata"`
}

func NewFeatureExtractorClient(baseURL string, token string) *FeatureExtractorClient {
	return &FeatureExtractorClient{
		baseURL: strings.TrimRight(baseURL, "/"),
		token:   token,
		client: &http.Client{
			Timeout: 10 * time.Second,
		},
	}
}

func (c *FeatureExtractorClient) Enqueue(ctx context.Context, payload featureExtractionRequest) error {
	url := c.baseURL + "/agents/feature_extractor/extract"
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
