DO $$
BEGIN
	CREATE TYPE public.item_status AS ENUM ('draft','active','ended','cancelled');
EXCEPTION
	WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS items (
	id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	seller_id uuid NOT NULL REFERENCES users(id),
	time_start timestamptz NOT NULL,
	time_end timestamptz NOT NULL,
	title text NOT NULL,
	description text,
	author text,
	features jsonb,
	year_created integer CHECK (year_created > 0),
	height double precision CHECK (height > 0),
	width double precision CHECK (width > 0),
	base_price bigint NOT NULL CHECK (base_price >= 0),
	increment bigint NOT NULL CHECK (increment > 0),
	status item_status NOT NULL DEFAULT 'draft',
	highest_bid_id uuid,
	highest_bid_amount BIGINT,
	highest_bidder_id uuid REFERENCES users(id),
	highest_bid_time timestamptz,
	created_at timestamptz NOT NULL DEFAULT now(),
	updated_at timestamptz NOT NULL DEFAULT now(),
	CHECK (time_end > time_start)
);

CREATE INDEX IF NOT EXISTS items_seller_id_idx ON items (seller_id);
CREATE INDEX IF NOT EXISTS item_status_time_end_idx ON items (status, time_end);
CREATE INDEX IF NOT EXISTS idx_items_draft_time_start ON items (time_start) WHERE status = 'draft';
CREATE INDEX IF NOT EXISTS idx_items_draft_active_time_end ON items (time_end) WHERE status IN ('draft', 'active');
CREATE INDEX IF NOT EXISTS items_highest_bid_amount_idx ON items (highest_bid_amount DESC);
