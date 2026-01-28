# Project Progress

This file is a lightweight checklist for the team.  
**Source of truth for detailed work:** GitHub Issues + PRs.

Legend:
- [x] Done
- [ ] Planned / In progress
- [~] Partially done (needs follow-up)

---

## Core Infrastructure
- [x] Repo structure + docs bootstrap (README, architecture, API contract, DB schema)
- [x] Dockerized Postgres
- [x] Dockerized pgAdmin
- [ ] Dockerized Go backend
- [ ] Dockerized Next.js frontend

## Database (Schema + Integrity)
- [ ] Enable `pgcrypto` (DB-generated UUIDs)
- [ ] Tables: `users`
- [ ] Tables: `items`
- [ ] Tables: `pictures`
- [ ] Tables: `bids`
- [ ] Indexes (browse + bid history)
- [ ] `updated_at` auto-update trigger (users/items)
- [ ] Bid validity enforcement trigger (min bid + timeframe + active status)

## Backend (Go)
### Auth
- [ ] `POST /auth/signup`
- [ ] `POST /auth/login`
- [ ] Email verification (tokens + verify endpoint) *(confirm CONTRACT is updated)*
- [ ] Auth middleware (protect seller/bid/upload endpoints)

### Items
- [ ] `GET /items` (browse + pagination)
- [ ] `GET /items/{id}` (item detail)
- [ ] `POST /items` (create listing)
- [ ] Status transitions (`draft → active → ended/cancelled`) *(if needed for demo)*

### Bids
- [ ] `POST /items/{id}/bids` (place bid)
- [ ] `GET /items/{id}/bids` (history)
- [ ] Concurrency-safe bidding (DB transaction + row lock OR DB trigger)

### Uploads / Pictures
- [ ] `POST /uploads` (optional signed URL)
- [ ] Store picture URLs/keys in `pictures`

### AI Support Endpoints
- [ ] `GET /ai/similar-items` (get similar items)
- [ ] `POST /ai/preview-in-room` (generate preview)

## Frontend (Next.js)
- [ ] Pages:
  - [ ] `/` browse items
  - [ ] `/login`
  - [ ] `/signup`
  - [ ] `/items/[itemId]`
  - [ ] `/items/new`

## AI Support
- [ ] Attribute extraction
- [ ] Similar items
- [ ] Preview in room
