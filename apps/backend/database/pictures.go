package database

import (
	"context"
	"database/sql"
)

type PictureDatabase struct {
	db *sql.DB
}

func NewPictureDatabase(db *sql.DB) *PictureDatabase {
	return &PictureDatabase{db: db}
}

type PicturePublic struct {
	ID        string `json:"id"`
	ItemID    string `json:"item_id"`
	URL       string `json:"url"`
	CreatedAt string `json:"created_at"`
}

func (r *PictureDatabase) CreatePictures(ctx context.Context, itemID string, urls []string) ([]PicturePublic, error) {
	if len(urls) == 0 {
		return []PicturePublic{}, nil
	}

	rows, err := r.db.QueryContext(ctx, `
		WITH ins AS (
			INSERT INTO pictures (item_id, url)
			SELECT $1::uuid, unnest($2::text[])
			RETURNING id::text, item_id::text, url, created_at
		)
		SELECT id, item_id, url, created_at
		FROM ins
		ORDER BY created_at ASC
	`, itemID, urls)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var out []PicturePublic
	for rows.Next() {
		var id, iid, url string
		var createdAt sql.NullTime
		if err := rows.Scan(&id, &iid, &url, &createdAt); err != nil {
			return nil, err
		}
		created := ""
		if createdAt.Valid {
			created = createdAt.Time.UTC().Format("2006-01-02T15:04:05Z07:00")
		}
		out = append(out, PicturePublic{
			ID: id, ItemID: iid, URL: url, CreatedAt: created,
		})
	}
	return out, rows.Err()
}

func (r *PictureDatabase) GetPicturesByItemID(ctx context.Context, itemID string) ([]PicturePublic, error) {
	rows, err := r.db.QueryContext(ctx, `
		SELECT id::text, item_id::text, url, created_at
		FROM pictures
		WHERE item_id = $1::uuid
		ORDER BY created_at ASC
	`, itemID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var out []PicturePublic
	for rows.Next() {
		var id, iid, url string
		var createdAt sql.NullTime
		if err := rows.Scan(&id, &iid, &url, &createdAt); err != nil {
			return nil, err
		}
		created := ""
		if createdAt.Valid {
			created = createdAt.Time.UTC().Format("2006-01-02T15:04:05Z07:00")
		}
		out = append(out, PicturePublic{
			ID: id, ItemID: iid, URL: url, CreatedAt: created,
		})
	}
	return out, rows.Err()
}

func (r *PictureDatabase) GetFirstPicturesByItemIDs(ctx context.Context, itemIDs []string) (map[string]PicturePublic, error) {
	out := make(map[string]PicturePublic)
	if len(itemIDs) == 0 {
		return out, nil
	}

	rows, err := r.db.QueryContext(ctx, `
		SELECT DISTINCT ON (item_id)
			id::text, item_id::text, url, created_at
		FROM pictures
		WHERE item_id = ANY($1::uuid[])
		ORDER BY item_id, created_at ASC
	`, itemIDs)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	for rows.Next() {
		var id, iid, url string
		var createdAt sql.NullTime
		if err := rows.Scan(&id, &iid, &url, &createdAt); err != nil {
			return nil, err
		}
		created := ""
		if createdAt.Valid {
			created = createdAt.Time.UTC().Format("2006-01-02T15:04:05Z07:00")
		}
		out[iid] = PicturePublic{
			ID: id, ItemID: iid, URL: url, CreatedAt: created,
		}
	}
	return out, rows.Err()
}
