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
- [x] Enable `pgcrypto` (DB-generated UUIDs)
- [x] Tables: `users`
- [x] Tables: `email_verification_tokens`
- [x] Tables: `items`
- [x] Tables: `pictures`
- [x] Tables: `bids`
- [x] Indexes (browse + bid history)
- [x] `updated_at` auto-update trigger (users/items)
- [x] Bid validity enforcement trigger (min bid + timeframe + active status)

## Backend (Go)
### Auth
- [x] `POST /auth/signup` (signup)
- [x] `POST /auth/login` (login)
- [x] `POST /auth/verify` (verify token)
- [x] `POST /auth/resend-verification` (resend email)
- [x] Auth Middleware
- [ ] Send Email Verification

### Items
- [x] `GET /items` (browse + pagination)
- [x] `GET /items/{id}` (item detail)
- [x] `POST /items` (create listing)
- [ ] Status transitions (`draft → active → ended/cancelled`)

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
