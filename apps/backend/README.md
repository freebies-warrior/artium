# Artium Backend (`apps/backend`)

This folder contains the **Go API server** for **Artium** — an auction-first art marketplace with optional AI extensions (Visualizer + feature extraction).

The backend is responsible for:
- **Auth** (signup/login/email verification)
- **Items** (listings, status flow `draft → active → ended`)
- **Pictures** (store object keys, not URLs)
- **Bids** (validation + race-safe bidding)
- **Uploads** (presigned URLs for object storage)
- **AI orchestration** (Visualizer jobs + Feature Extractor callbacks)

> Source of truth for endpoints and response shapes: `docs/api/CONTRACT.md` (repo root).  
> Architecture context: `docs/architecture.md` and DB schema: `docs/db/schema.md`.

---

## Quick start (local)

### 1) Prerequisites
- Go **1.22+** (or whatever `go.mod` specifies)
- Docker (recommended for Postgres)
- Node.js only if you’re running the frontend too

### 2) Start Postgres (Docker)
If you have a `docker-compose.yml` at repo root, use it:

```bash
# from repo root
docker compose up -d postgres pgadmin
```

Or run Postgres manually.

### 3) Configure environment
Create `apps/backend/.env` (or export env vars in your shell). For the canonical env reference, see `docs/env.md` in the repo root.

```bash
# Server
PORT=8080
ENV=dev

# Database
DATABASE_URL=postgres://postgres:postgres@localhost:5432/artium?sslmode=disable

# Auth
JWT_SECRET=change-me
INTERNAL_TOKEN=change-me-too

# Object storage (Cloudflare R2 / S3-compatible)
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET=...
```

### 4) Run the backend
From repo root:

```bash
cd apps/backend
go run .
```

Backend default base URL (local): `http://localhost:8080`

---

## Responsibilities (what belongs here)

### Auth
- Create users and store hashed passwords (never plaintext).
- Issue JWT for authenticated requests.
- Protect seller and bidding endpoints.
- Email verification tokens (see `email_verification_tokens` in schema).

### Items (Listings)
- Create listings and validate auction times.
- Enforce status transitions: `draft → active → ended` (optional `cancelled`).
- Return item summaries and item detail.

### Pictures / Object keys
- DB stores **object keys** (e.g., `pictures.key`) rather than signed URLs.
- Signed URLs (GET/PUT) are generated on demand.

### Bids (race-safe)
Bidding must be correct with concurrent users.
Recommended pattern (from architecture doc):
- Start a transaction
- `SELECT ... FOR UPDATE` on the item row
- validate minimum allowed bid
- insert bid
- update cached fields (`highest_bid_amount` etc.) if used
- commit

### AI orchestration (backend stays source of truth)
- Visualizer jobs are created in backend DB and processed asynchronously.
- Feature extraction writes into `items.features` via an internal endpoint.
- AI services must **not write to Postgres directly**.

---

## Database & schema

Reference:
- `docs/db/schema.md`

Tables (MVP):
- `users`
- `email_verification_tokens`
- `items` (includes `features` JSONB)
- `pictures`
- `bids`
- `visualization_jobs`

**Money format**
- Stored and returned as **integers in SGD dollars** (not cents), per API contract.

---

## Object storage (Cloudflare R2)

The backend issues:
- **Presigned PUT** URLs for direct uploads (frontend uploads images directly)
- **Presigned GET** URLs for private reads (short-lived)

Key rule:
- **Do not** store signed URLs in Postgres — store keys and sign on demand.

---

## API overview (high-level)

See `docs/api/CONTRACT.md` for full details. Common endpoints:

### Auth
- `POST /auth/signup`
- `POST /auth/login`
- `POST /auth/verify`
- `POST /auth/resend-verification`

### Items
- `GET /items`
- `GET /items/{item_id}`
- `POST /items` (auth required)

### Bids
- `POST /items/{item_id}/bids` (auth required)
- `GET /items/{item_id}/bids`

### Uploads
- `POST /uploads/presign` (auth required)

### Visualizer (async jobs)
- `POST /visualizations` (auth required)
- `GET /visualizations/{job_id}` (auth required)
- `PUT /visualizations/{job_id}` (internal only; called by AI backend)

### Feature extractor internal callback
- `PUT /items/{item_id}/features` (internal only)

---

## Local dev tips

### CORS
If running frontend locally, ensure your backend allows requests from `http://localhost:3000` (dev only).

### Logging
Prefer structured logs (request ID + route + latency). Avoid logging:
- JWTs
- internal tokens
- full presigned URLs

### Timeouts
Outbound calls (AI services, R2 signing) should have sane timeouts.

---

## Testing
If tests exist, run from `apps/backend`:

```bash
go test ./... -cover -coverprofile=coverage.out -tags=unit
```

If you have integration tests needing Postgres, run with Docker first.

---

## Deployment notes (cheap/free-friendly)
- Deploy backend as a container to a cheap/free compute platform
- Keep Postgres separate (managed if possible)
- R2 is S3-compatible and typically works well with presigned URLs

---

## References
- `docs/architecture.md`
- `docs/api/CONTRACT.md`
- `docs/db/schema.md`
