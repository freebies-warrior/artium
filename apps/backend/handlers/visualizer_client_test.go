package handlers

import (
	"encoding/json"
	"testing"
)

func TestVisualizerClientPayloadJSONMatchesContract(t *testing.T) {
	payload := visualizeInstallationReq{
		RoomURL:        "https://example.com/room.jpg",
		ArtURL:         "https://example.com/art.jpg",
		UploadImageURL: "https://example.com/upload.jpg",
		ResultImageKey: "visualizations/job-123/result.jpg",
		JobID:          "job-123",
		ItemDimensions: &struct {
			Width  float64 `json:"width"`
			Height float64 `json:"height"`
		}{
			Width:  60.5,
			Height: 40.25,
		},
	}

	got, err := json.Marshal(payload)
	if err != nil {
		t.Fatalf("marshal payload: %v", err)
	}

	want := `{"room_url":"https://example.com/room.jpg","art_url":"https://example.com/art.jpg","upload_image_url":"https://example.com/upload.jpg","result_image_key":"visualizations/job-123/result.jpg","job_id":"job-123","item_dimensions":{"width":60.5,"height":40.25}}`
	if string(got) != want {
		t.Fatalf("unexpected payload JSON\nwant: %s\ngot:  %s", want, string(got))
	}
}
