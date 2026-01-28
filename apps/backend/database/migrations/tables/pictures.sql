CREATE TABLE IF NOT EXISTS pictures (
	id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	item_id uuid NOT NULL REFERENCES items(id) ON DELETE CASCADE,
	url text NOT NULL,
	created_at timestamptz NOT NULL DEFAULT now()
);
