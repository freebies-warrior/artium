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
	base_price bigint NOT NULL CHECK (base_price >= 0),
	increment bigint NOT NULL CHECK (increment > 0),
	status item_status NOT NULL DEFAULT 'draft',
	created_at timestamptz NOT NULL DEFAULT now(),
	updated_at timestamptz NOT NULL DEFAULT now(),
	CHECK (time_end > time_start)
);
