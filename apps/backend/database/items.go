package database

import (
	"context"
	"database/sql"
	"encoding/base64"
	"errors"
	"fmt"
	"strings"
	"time"
)

type ItemDatabase struct {
	db *sql.DB
}

func NewItemDatabase(db *sql.DB) *ItemDatabase {
	return &ItemDatabase{db: db}
}

type Item struct {
	ID               string          `json:"id"`
	SellerID         string          `json:"seller_id"`
	SellerUsername   *string         `json:"seller_username,omitempty"`
	Title            string          `json:"title"`
	Description      *string         `json:"description,omitempty"`
	Author           *string         `json:"author,omitempty"`
	Features         any             `json:"features,omitempty"`
	YearCreated      *int            `json:"year_created,omitempty"`
	Height           *float64        `json:"height,omitempty"`
	Width            *float64        `json:"width,omitempty"`
	BasePrice        int64           `json:"base_price"`
	Increment        int64           `json:"increment"`
	Status           string          `json:"status"`
	TimeStart        time.Time       `json:"time_start"`
	TimeEnd          time.Time       `json:"time_end"`
	HighestBidId     *string         `json:"highest_bid_id,omitempty"`
	HighestBidAmount *int64          `json:"highest_bid_amount,omitempty"`
	HighestBidderId  *string         `json:"highest_bidder_id,omitempty"`
	HighestBidTime   *time.Time      `json:"highest_bid_time,omitempty"`
	CreatedAt        time.Time       `json:"created_at"`
	UpdatedAt        time.Time       `json:"updated_at"`
	Pictures         []PicturePublic `json:"pictures,omitempty"` // filled in handler
}

type CreateItemArgs struct {
	SellerID    string
	Title       string
	Description *string
	Author      *string
	BasePrice   int64
	Increment   int64
	YearCreated *int
	Height      *float64
	Width       *float64
	TimeStart   time.Time
	TimeEnd     time.Time
}

func (r *ItemDatabase) CreateItem(ctx context.Context, a CreateItemArgs) (Item, error) {
	var (
		desc   sql.NullString
		auth   sql.NullString
		year   sql.NullInt32
		height sql.NullFloat64
		width  sql.NullFloat64
	)

	if a.Description != nil {
		desc = sql.NullString{String: *a.Description, Valid: true}
	}
	if a.Author != nil {
		auth = sql.NullString{String: *a.Author, Valid: true}
	}
	if a.YearCreated != nil {
		year = sql.NullInt32{Int32: int32(*a.YearCreated), Valid: true}
	}
	if a.Height != nil {
		height = sql.NullFloat64{Float64: *a.Height, Valid: true}
	}
	if a.Width != nil {
		width = sql.NullFloat64{Float64: *a.Width, Valid: true}
	}

	var (
		outDesc sql.NullString
		outAuth sql.NullString
		outYear sql.NullInt32
		outH    sql.NullFloat64
		outW    sql.NullFloat64

		outHighestBidID     sql.NullString
		outHighestBidAmount sql.NullInt64
		outHighestBidderID  sql.NullString
		outHighestBidTime   sql.NullTime

		featStr string
	)

	var it Item
	err := r.db.QueryRowContext(ctx, `
		INSERT INTO items (
			seller_id, time_start, time_end,
			title, description, author,
			year_created, height, width,
			base_price, increment, status
		) VALUES (
			$1::uuid, $2, $3,
			$4, $5, $6,
			$7, $8, $9,
			$10, $11, 'active'
		)
		RETURNING
			id::text, seller_id::text,
			title, description, author,
			COALESCE(features::text, '')::text,
			year_created, height, width,
			base_price, increment, status::text,
			time_start, time_end,
			highest_bid_id::text, highest_bid_amount,
			highest_bidder_id::text, highest_bid_time,
			created_at, updated_at
	`, a.SellerID, a.TimeStart, a.TimeEnd,
		a.Title, desc, auth,
		year, height, width,
		a.BasePrice, a.Increment,
	).Scan(
		&it.ID, &it.SellerID,
		&it.Title, &outDesc, &outAuth,
		&featStr,
		&outYear, &outH, &outW,
		&it.BasePrice, &it.Increment, &it.Status,
		&it.TimeStart, &it.TimeEnd,
		&outHighestBidID, &outHighestBidAmount,
		&outHighestBidderID, &outHighestBidTime,
		&it.CreatedAt, &it.UpdatedAt,
	)
	if err != nil {
		return Item{}, err
	}

	if outDesc.Valid {
		it.Description = &outDesc.String
	}
	if outAuth.Valid {
		it.Author = &outAuth.String
	}
	if outYear.Valid {
		v := int(outYear.Int32)
		it.YearCreated = &v
	}
	if outH.Valid {
		v := outH.Float64
		it.Height = &v
	}
	if outW.Valid {
		v := outW.Float64
		it.Width = &v
	}
	if outHighestBidID.Valid {
		v := outHighestBidID.String
		it.HighestBidId = &v
	}
	if outHighestBidAmount.Valid {
		v := outHighestBidAmount.Int64
		it.HighestBidAmount = &v
	}
	if outHighestBidderID.Valid {
		v := outHighestBidderID.String
		it.HighestBidderId = &v
	}
	if outHighestBidTime.Valid {
		v := outHighestBidTime.Time
		it.HighestBidTime = &v
	}

	_ = featStr // features left nil for now
	return it, nil
}

var ErrNotFound = errors.New("not_found")

func (r *ItemDatabase) GetItemByID(ctx context.Context, itemID string) (Item, error) {
	var (
		outDesc sql.NullString
		outAuth sql.NullString
		outYear sql.NullInt32
		outH    sql.NullFloat64
		outW    sql.NullFloat64

		outSellerUsername sql.NullString

		outHighestBidID     sql.NullString
		outHighestBidAmount sql.NullInt64
		outHighestBidderID  sql.NullString
		outHighestBidTime   sql.NullTime

		featStr string
	)

	var it Item
	err := r.db.QueryRowContext(ctx, `
		SELECT
			i.id::text, i.seller_id::text, 
			u.username AS seller_username,
			i.title, i.description, i.author,
			COALESCE(i.features::text, '')::text,
			i.year_created, i.height, i.width,
			i.base_price, i.increment, i.status::text,
			i.time_start, i.time_end,
			i.highest_bid_id::text, i.highest_bid_amount,
			i.highest_bidder_id::text, i.highest_bid_time,
			i.created_at, i.updated_at
		FROM items i
		JOIN users u ON u.id = i.seller_id
		WHERE i.id = $1::uuid
	`, itemID).Scan(
		&it.ID, &it.SellerID,
		&outSellerUsername,
		&it.Title, &outDesc, &outAuth,
		&featStr,
		&outYear, &outH, &outW,
		&it.BasePrice, &it.Increment, &it.Status,
		&it.TimeStart, &it.TimeEnd,
		&outHighestBidID, &outHighestBidAmount,
		&outHighestBidderID, &outHighestBidTime,
		&it.CreatedAt, &it.UpdatedAt,
	)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return Item{}, ErrNotFound
		}
		return Item{}, err
	}

	if outSellerUsername.Valid {
		it.SellerUsername = &outSellerUsername.String
	}
	if outDesc.Valid {
		it.Description = &outDesc.String
	}
	if outAuth.Valid {
		it.Author = &outAuth.String
	}
	if outYear.Valid {
		v := int(outYear.Int32)
		it.YearCreated = &v
	}
	if outH.Valid {
		v := outH.Float64
		it.Height = &v
	}
	if outW.Valid {
		v := outW.Float64
		it.Width = &v
	}
	if outHighestBidID.Valid {
		v := outHighestBidID.String
		it.HighestBidId = &v
	}
	if outHighestBidAmount.Valid {
		v := outHighestBidAmount.Int64
		it.HighestBidAmount = &v
	}
	if outHighestBidderID.Valid {
		v := outHighestBidderID.String
		it.HighestBidderId = &v
	}
	if outHighestBidTime.Valid {
		v := outHighestBidTime.Time
		it.HighestBidTime = &v
	}

	_ = featStr
	return it, nil
}

type ListItemsParams struct {
	Limit    int
	Cursor   string
	Status   string
	SellerID string
	Query    string
}

func makeCursor(createdAt time.Time, id string) string {
	raw := fmt.Sprintf("%s|%s", createdAt.UTC().Format(time.RFC3339Nano), id)
	return base64.RawURLEncoding.EncodeToString([]byte(raw))
}

func parseCursor(cur string) (*time.Time, *string, error) {
	b, err := base64.RawURLEncoding.DecodeString(cur)
	if err != nil {
		return nil, nil, err
	}
	parts := strings.SplitN(string(b), "|", 2)
	if len(parts) != 2 {
		return nil, nil, fmt.Errorf("bad cursor")
	}
	t, err := time.Parse(time.RFC3339Nano, parts[0])
	if err != nil {
		return nil, nil, err
	}
	id := parts[1]
	return &t, &id, nil
}

func (r *ItemDatabase) ListItems(ctx context.Context, p ListItemsParams) ([]Item, *string, error) {
	limit := p.Limit
	if limit <= 0 {
		limit = 20
	}
	if limit > 100 {
		limit = 100
	}

	status := strings.ToLower(strings.TrimSpace(p.Status))
	var statusParam any = nil
	if status != "" {
		switch status {
		case "draft", "active", "ended", "cancelled":
			statusParam = status
		default:
			return nil, nil, fmt.Errorf("invalid status")
		}
	}

	sellerID := strings.TrimSpace(p.SellerID)
	var sellerParam any = nil
	if sellerID != "" {
		sellerParam = sellerID
	}

	q := strings.TrimSpace(p.Query)
	qLike := "%" + q + "%"

	hasCursor := false
	var curT time.Time
	var curID string
	if strings.TrimSpace(p.Cursor) != "" {
		t, id, err := parseCursor(p.Cursor)
		if err != nil {
			return nil, nil, err
		}
		hasCursor = true
		curT = *t
		curID = *id
	} else {
		curT = time.Unix(0, 0).UTC()
		curID = "00000000-0000-0000-0000-000000000000"
	}

	rows, err := r.db.QueryContext(ctx, `
        SELECT
            i.id::text, i.seller_id::text,
			u.username AS seller_username,
            i.title, i.author,
            i.base_price, i.increment, i.status::text,
			i.year_created, i.height, i.width,
            i.time_start, i.time_end,
			i.highest_bid_id::text, i.highest_bid_amount,
			i.highest_bidder_id::text, i.highest_bid_time,
            i.created_at, i.updated_at
        FROM items i
		JOIN users u ON u.id = i.seller_id
        WHERE
            ($1::item_status IS NULL OR i.status = $1::item_status)
			AND ($2::uuid IS NULL OR i.seller_id = $2::uuid)
            AND ($3 = '' OR i.title ILIKE $4 OR COALESCE(i.author, '') ILIKE $4)
            AND (NOT $5 OR (i.created_at, i.id) < ($6, $7::uuid))
        ORDER BY i.created_at DESC, i.id DESC
        LIMIT $8
    `, statusParam, sellerParam, q, qLike, hasCursor, curT, curID, limit+1)
	if err != nil {
		return nil, nil, err
	}
	defer rows.Close()

	items := make([]Item, 0, limit+1)
	for rows.Next() {
		var it Item

		var outSellerUsername sql.NullString
		var author sql.NullString
		var outYear sql.NullInt32
		var outH sql.NullFloat64
		var outW sql.NullFloat64

		var outHighestBidID sql.NullString
		var outHighestBidAmount sql.NullInt64
		var outHighestBidderID sql.NullString
		var outHighestBidTime sql.NullTime

		if err := rows.Scan(
			&it.ID, &it.SellerID,
			&outSellerUsername,
			&it.Title, &author,
			&it.BasePrice, &it.Increment, &it.Status,
			&outYear, &outH, &outW,
			&it.TimeStart, &it.TimeEnd,
			&outHighestBidID, &outHighestBidAmount,
			&outHighestBidderID, &outHighestBidTime,
			&it.CreatedAt, &it.UpdatedAt,
		); err != nil {
			return nil, nil, err
		}

		if outSellerUsername.Valid {
			it.SellerUsername = &outSellerUsername.String
		}
		if author.Valid {
			it.Author = &author.String
		}
		if outYear.Valid {
			v := int(outYear.Int32)
			it.YearCreated = &v
		}
		if outH.Valid {
			v := outH.Float64
			it.Height = &v
		}
		if outW.Valid {
			v := outW.Float64
			it.Width = &v
		}
		if outHighestBidID.Valid {
			v := outHighestBidID.String
			it.HighestBidId = &v
		}
		if outHighestBidAmount.Valid {
			v := outHighestBidAmount.Int64
			it.HighestBidAmount = &v
		}
		if outHighestBidderID.Valid {
			v := outHighestBidderID.String
			it.HighestBidderId = &v
		}
		if outHighestBidTime.Valid {
			v := outHighestBidTime.Time
			it.HighestBidTime = &v
		}

		items = append(items, it)
	}
	if err := rows.Err(); err != nil {
		return nil, nil, err
	}

	var next *string
	if len(items) > limit {
		last := items[limit-1]
		nc := makeCursor(last.CreatedAt, last.ID)
		next = &nc
		items = items[:limit]
	}

	return items, next, nil
}

func (r *ItemDatabase) UpdateItemStatus(ctx context.Context, itemID string) error {
	_, err := r.db.ExecContext(ctx, `SELECT refresh_item_status($1::uuid)`, itemID)
	return err
}

func (r *ItemDatabase) UpdateItemFeatures(ctx context.Context, itemID string, featuresJSON string) error {
	res, err := r.db.ExecContext(ctx, `
		UPDATE items
		SET features = $2::jsonb
		WHERE id = $1::uuid
	`, itemID, featuresJSON)
	if err != nil {
		return err
	}

	n, err := res.RowsAffected()
	if err != nil {
		return err
	}
	if n == 0 {
		return ErrNotFound
	}
	return nil
}

func (r *ItemDatabase) Exists(ctx context.Context, itemID string) (bool, error) {
	var exists bool
	err := r.db.QueryRowContext(ctx,
		`SELECT EXISTS (SELECT 1 FROM items WHERE id = $1)`,
		itemID,
	).Scan(&exists)
	return exists, err
}
