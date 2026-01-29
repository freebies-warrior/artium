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
	Key       string `json:"key"`
	CreatedAt string `json:"created_at"`
}

func (r *PictureDatabase) CreatePictures(ctx context.Context, itemID string, keys []string) ([]PicturePublic, error) {
	if len(keys) == 0 {
		return []PicturePublic{}, nil
	}

	rows, err := r.db.QueryContext(ctx, `
		WITH ins AS (
			INSERT INTO pictures (item_id, key)
			SELECT $1::uuid, unnest($2::text[])
			RETURNING id::text, item_id::text, key, created_at
		)
		SELECT id, item_id, key, created_at
		FROM ins
		ORDER BY created_at ASC
	`, itemID, keys)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var out []PicturePublic
	for rows.Next() {
		var id, iid, key string
		var createdAt sql.NullTime
		if err := rows.Scan(&id, &iid, &key, &createdAt); err != nil {
			return nil, err
		}
		created := ""
		if createdAt.Valid {
			created = createdAt.Time.UTC().Format("2006-01-02T15:04:05Z07:00")
		}
		out = append(out, PicturePublic{
			ID: id, ItemID: iid, Key: key, CreatedAt: created,
		})
	}
	return out, rows.Err()
}

func (r *PictureDatabase) GetPicturesByItemID(ctx context.Context, itemID string) ([]PicturePublic, error) {
	rows, err := r.db.QueryContext(ctx, `
		SELECT id::text, item_id::text, key, created_at
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
		var id, iid, key string
		var createdAt sql.NullTime
		if err := rows.Scan(&id, &iid, &key, &createdAt); err != nil {
			return nil, err
		}
		created := ""
		if createdAt.Valid {
			created = createdAt.Time.UTC().Format("2006-01-02T15:04:05Z07:00")
		}
		out = append(out, PicturePublic{
			ID: id, ItemID: iid, Key: key, CreatedAt: created,
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
			id::text, item_id::text, key, created_at
		FROM pictures
		WHERE item_id = ANY($1::uuid[])
		ORDER BY item_id, created_at ASC
	`, itemIDs)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	for rows.Next() {
		var id, iid, key string
		var createdAt sql.NullTime
		if err := rows.Scan(&id, &iid, &key, &createdAt); err != nil {
			return nil, err
		}
		created := ""
		if createdAt.Valid {
			created = createdAt.Time.UTC().Format("2006-01-02T15:04:05Z07:00")
		}
		out[iid] = PicturePublic{
			ID: id, ItemID: iid, Key: key, CreatedAt: created,
		}
	}
	return out, rows.Err()
}
