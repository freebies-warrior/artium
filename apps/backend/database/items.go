package database

import (
	"context"
	"database/sql"
)

type ItemDatabase struct {
	db *sql.DB
}

func NewItemDatabase(db *sql.DB) *ItemDatabase {
	return &ItemDatabase{db: db}
}

func (r *ItemDatabase) Exists(ctx context.Context, itemID string) (bool, error) {
	var exists bool
	err := r.db.QueryRowContext(ctx,
		`SELECT EXISTS (SELECT 1 FROM items WHERE id = $1)`,
		itemID,
	).Scan(&exists)
	return exists, err
}
