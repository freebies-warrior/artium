# Artium Frontend (`apps/frontend`)

The **Artium Web App** is a **Next.js** frontend for an auction-first art marketplace with optional AI features (Visualizer + feature extraction).

It talks to the **Go backend** (`apps/backend`) via HTTP JSON APIs, and renders:
- Browse / search auction listings
- Item detail pages (images, bid info, bid history)
- Seller flows (create listing, attach images)
- AI flows (e.g., “View in your space” visualizer job + showing extracted features)

> Source of truth for endpoints and response shapes: `docs/api/CONTRACT.md` (repo root).

---

## Quick start (local)

### 1) Prerequisites
- Node.js **18+** (20+ recommended)
- One package manager: `npm` / `pnpm` / `yarn`
- Go backend running locally (default: `http://localhost:8080`)

### 2) Install dependencies
From repo root:
```bash
cd apps/frontend

# pick ONE
npm install
# pnpm install
# yarn
```

### 3) Configure environment
Create `apps/frontend/.env.local`:

```bash
# See canonical env reference: `docs/env.md`
BACKEND_URL=http://localhost:8080
JWT_SECRET=<JWT_SECRET>
```

`BACKEND_URL` is server-side only.
`JWT_SECRET` is required for the auth route.

### 4) Run the dev server
```bash
# pick ONE
npm run dev
# pnpm dev
# yarn dev
```

Open:
- `http://localhost:3000`

---

## How the frontend connects to the backend

### API base URL
See `docs/env.md` for the canonical environment variables.
The frontend server-side API routes should use `BACKEND_URL`.

### Auth
Protected endpoints require a Bearer token (JWT), per `docs/api/CONTRACT.md`.
`JWT_SECRET` is required for the auth route.

Common patterns (implementation-dependent):
- Store token in memory + persist in localStorage (fast hackathon MVP)
- Prefer HTTP-only cookies for better security (post-hackathon)

---

## Key user flows (what to demo)

### Buyer flow
1. Browse items (`GET /items`)
2. Open item page (`GET /items/{item_id}`)
3. Place bid (`POST /items/{item_id}/bids`)
4. See bid history (`GET /items/{item_id}/bids`)

### Seller flow
1. Upload item images (presigned upload via `POST /uploads/presign`)
2. Create item listing (`POST /items` with `picture_keys`)
3. (Optional) publish item / status transitions (if implemented)

### AI flows
#### Visualizer: “View in your space”
1. Upload room photo via `POST /uploads/presign`
2. Create visualizer job via `POST /visualizations`
3. Poll job status via `GET /visualizations/{job_id}`
4. Render result image + description when status is `succeeded`

#### Feature extraction (async)
- Item features may be `null` immediately after creation.
- Frontend should render a “Generating…” state and refresh when features arrive.

---

## Scripts

Typical Next.js scripts (check your `package.json` for the exact list):
```bash
npm run dev      # start dev server
npm run build    # production build
npm run start    # start production server
npm run lint     # lint
npm run test     # tests (if configured)
```

---

## Recommended project conventions

### UI states (important for hackathon polish)
- **Loading states** (skeletons/spinners) for:
  - item grid
  - item detail page
  - bid submission
  - visualizer job polling
- **Error states** with actionable messages:
  - unauthenticated -> prompt login
  - forbidden -> explain why (seller cannot bid / auction ended)
  - AI failure -> suggest retry

### Data formatting
- Money values are **integers in SGD dollars** (not cents), per `docs/api/CONTRACT.md`.
- Timestamps are ISO-8601 UTC strings (render in local time for UX).

---

## Folder structure (expected)

This varies by Next.js router choice, but common patterns:

### App Router
```
apps/frontend/
  app/
    page.tsx
    items/[itemId]/page.tsx
  components/
  lib/
  public/
```

### Pages Router
```
apps/frontend/
  pages/
    index.tsx
    items/[itemId].tsx
  components/
  lib/
  public/
```

---

## Troubleshooting

### API requests fail (CORS / network)
- Ensure Go backend is running at `BACKEND_URL`.
- Check browser devtools Network tab for the failing URL.
- Confirm the endpoint exists in `docs/api/CONTRACT.md`.

### Auth keeps “forgetting”
- Verify where token is stored (cookie vs localStorage).
- Confirm requests include `Authorization: Bearer <token>` for protected endpoints.

### Images don’t load
- If using object storage with signed URLs, they expire.
- Ensure frontend requests fresh signed GET URLs when needed (or backend includes `result_image_url` in job status).

---

## References
- `docs/architecture.md`
- `docs/api/CONTRACT.md`
- `docs/db/schema.md`
