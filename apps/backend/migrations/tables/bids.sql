CREATE TABLE IF NOT EXISTS bids (
	id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	user_id uuid NOT NULL REFERENCES users(id),
	item_id uuid NOT NULL REFERENCES items(id) ON DELETE CASCADE,
	price bigint NOT NULL CHECK (price > 0),
	timestamp timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS bids_item_id_timestamp_idx ON bids(item_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS bids_user_id_timestamp_idx ON bids(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS bids_item_price_desc_idx ON bids(item_id, price DESC);