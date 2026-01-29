package database

import (
	"context"
	"database/sql"
	"time"
)

type Bid struct {
	ID        string    `json:"id"`
	UserID    string    `json:"user_id"`
	ItemID    string    `json:"item_id"`
	Price     int64     `json:"price"`
	Timestamp time.Time `json:"timestamp"`
}

type BidDatabase struct {
	db *sql.DB
}

func NewBidDatabase(db *sql.DB) *BidDatabase {
	return &BidDatabase{db: db}
}

func (r *BidDatabase) CreateBid(ctx context.Context, userID, itemID string, price int64) (Bid, error) {
	var bid Bid
	err := r.db.QueryRowContext(ctx,
		`INSERT INTO bids (user_id, item_id, price)
		 VALUES ($1, $2, $3)
		 RETURNING id::text, user_id::text, item_id::text, price, timestamp`,
		userID, itemID, price,
	).Scan(&bid.ID, &bid.UserID, &bid.ItemID, &bid.Price, &bid.Timestamp)
	return bid, err
}

func (r *BidDatabase) ListBidsForItem(ctx context.Context, itemID string) ([]Bid, error) {
	rows, err := r.db.QueryContext(ctx,
		`SELECT id::text, user_id::text, item_id::text, price, timestamp
		 FROM bids
		 WHERE item_id = $1
		 ORDER BY timestamp DESC`,
		itemID,
	)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	bids := []Bid{}
	for rows.Next() {
		var bid Bid
		if err := rows.Scan(&bid.ID, &bid.UserID, &bid.ItemID, &bid.Price, &bid.Timestamp); err != nil {
			return nil, err
		}
		bids = append(bids, bid)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return bids, nil
}
