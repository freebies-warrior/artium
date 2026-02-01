CREATE TABLE IF NOT EXISTS visualization_jobs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    item_id uuid NOT NULL REFERENCES items(id) ON DELETE CASCADE,

    item_image_key text NOT NULL,
    room_image_key text NOT NULL,

    status text NOT NULL DEFAULT 'queued',
    result_image_key text,
    result_description text,
    error_message text,

    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT visualization_jobs_status_check
        CHECK (status IN ('queued','processing','succeeded','failed'))
);

CREATE INDEX IF NOT EXISTS visualization_jobs_user_id_created_at_idx
ON visualization_jobs(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS visualization_jobs_item_id_created_at_idx
ON visualization_jobs(item_id, created_at DESC);

CREATE INDEX IF NOT EXISTS visualization_jobs_status_updated_at_idx
ON visualization_jobs(status, updated_at DESC);