CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- store SHA-256(token) (32 bytes)
    token_hash bytea NOT NULL UNIQUE,

    expires_at timestamptz NOT NULL,
    used_at    timestamptz NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS evt_user_id_idx ON email_verification_tokens(user_id);
CREATE INDEX IF NOT EXISTS evt_expires_at_idx ON email_verification_tokens(expires_at);
