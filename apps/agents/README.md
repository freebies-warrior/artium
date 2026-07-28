# Artium Agents Service (`apps/agents`)

This folder contains the **AI Agents backend** for **Artium** — a small HTTP service that runs AI-powered workflows used by the main Go backend:
- **Visualizer**: merge an artwork image with a user “room photo” to generate a preview image + caption.
- **Price Valuator**: analyze uploaded item images and produce structured report for price valuation using extracted feature.

> **Design principle:** the Agents service **does not write to Postgres directly**.  
> It processes inputs, returning an OK response before then doing another requests back into the Go backend’s internal endpoints to persist results.

---

## Table of Contents
- [What this service does](#what-this-service-does)
- [How it integrates with the Go backend](#how-it-integrates-with-the-go-backend)
- [Endpoints](#endpoints)
  - [Visualizer](#visualizer)
  - [Feature Extractor](#feature-extractor)
- [Security](#security)
- [Local development](#local-development)
- [Project structure](#project-structure)
- [Adding a new agent](#adding-a-new-agent)
- [Troubleshooting](#troubleshooting)

---

## What this service does

### 1) Visualizer (preview in room)
Given:
- an artwork image (from object storage)
- a room photo uploaded by the user
- item dimensions (optional)

The agent:
1. downloads both images (typically from **signed GET URLs** issued by Go backend)
2. runs a visualization pipeline (overlay / perspective / styling)
3. uploads the output image to object storage (typically via **signed PUT URL**)
4. returns **immediately** to the caller (Go backend) with `{ ok: true }`
5. updates job status/results via the Go backend (callback or internal job update endpoint)

### 2) Price valuator
Given:
- item images (keys + signed GET URLs)
- optional metadata (title, author, year)
- a callback URL into Go backend

The agent:
1. downloads images
2. extracts a `features` JSON object (medium, style, palette, mood, etc.)
3. Calculates an estimated price using features extracted from the image, the artwork’s socioeconomic context, and surrounding market conditions.

---

## How it integrates with the Go backend

Typical flow:
1. **Frontend** uploads images to object storage using presigned PUT URLs from Go backend.
2. **Go backend** creates DB records (item, pictures, visualization job).
3. **Go backend** calls **Agents service** with:
   - signed GET URLs for inputs (artwork/room/item images)
   - signed PUT URL (or upload endpoint) for outputs
   - `job_id` / `item_id` and a **callback URL** for result persistence
4. **Agents service** processes async and uses internal endpoints to update state/results.

---

## Endpoints

> Paths below reflect the current documented contract.  
> If you rename endpoints, update `docs/api/CONTRACT.md` immediately.

### Visualizer

**POST** `/agents/visualizer/visualize_installation`  
**Auth:** internal-only header

**Headers**
- `X-Internal-Token: <secret>`

**Request**
```json
{
  "room_url": "https://.../rooms/<uid>/...jpg",
  "art_url": "https://.../items/<item_id>/main.jpg",
  "upload_image_url": "https://.../visualizations/<job_id>/result.jpg",
  "result_image_key": "visualizations/<job_id>/result.jpg",
  "item_dimensions": { "width": 60, "height": 40 },
  "job_id": "uuid"
}
```

**Response**
```json
{ "ok": true }
```

**Notes**
- `room_url` and `art_url` are typically **presigned GET URLs**.
- `upload_image_url` is typically a **presigned PUT URL** (or an upload endpoint).
- This endpoint should **ACK quickly** and do the heavy work asynchronously when possible.

---

### Feature Extractor

**POST** `/agents/feature_extractor/extract_item_features`  
**Auth:** internal-only header

**Headers**
- `X-Internal-Token: <secret>`

**Request**
```json
{
  "item_id": "uuid",
  "image_keys": [
    "uploads/<uid>/...jpg",
    "uploads/<uid>/...jpg"
  ],
  "image_get_urls": [
    "https://...signed-get-url...",
    "https://...signed-get-url..."
  ],
  "callback_url": "https://<go-backend>/internal/items/<item_id>/features",
  "metadata": {
    "author": "optional",
    "title": "optional",
    "year": "optional"
  }
}
```

**Response**
```json
{ "ok": true }
```

**Notes**
- The worker downloads images from `image_get_urls`, then `POST/PUT`s results to `callback_url`.
- The callback must be **idempotent** (safe to retry).

---

## Security

This service is **internal-only**.

Minimum requirements:
- Require a shared secret header: `X-Internal-Token`.
- Reject requests without a valid token.
- Never log secrets, tokens, or full presigned URLs.

Recommended:
- Add request IDs + structured logs.
- Rate-limit internal callers if needed.
- Consider HMAC signatures for callback payloads if you want stronger integrity.

---

## Local development

> This repo can be set up with either `pip` or a tool like `poetry/uv`.  
> Use whichever matches the files present in this folder (`requirements.txt` / `pyproject.toml`).

### Option A: `pip` + venv
```bash
cd apps/agents
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run dev server (adjust module path if your app entrypoint differs)
uvicorn app:app --reload --host 0.0.0.0 --port 8001
```

### Option B: Docker (recommended for parity)
If your repo provides a Dockerfile for agents:
```bash
docker build -t artium-agents .
docker run --rm -p 8001:8001 --env-file .env artium-agents
```

### Environment variables
See the canonical env reference in [`docs/env.md`](../../docs/env.md).

`MANUS_API_KEY` is optional and only needed when the Manus integration is enabled.

---

## Adding a new agent

1. Create a new module under `app/agents/<new_agent>.py`
2. Add a router with a stable prefix, e.g.:
   - `/agents/<new_agent>/run`
3. Add an input schema (Pydantic model) with explicit validation.
4. Implement:
   - download input(s)
   - run model/pipeline
   - upload output(s) if any
   - callback to Go backend (do not write DB directly)
5. Update **`docs/api/CONTRACT.md`** with request/response examples.
6. (Optional) Add a minimal integration test using a mocked Go backend callback endpoint.

---

## Troubleshooting

### “401 / 403 Unauthorized”
- Check `X-Internal-Token` is present and matches server config.
- Confirm the Go backend is using the correct secret.

### Timeouts / slow responses
- Keep the HTTP endpoint fast (ACK early).
- Move heavy processing to background tasks/workers if possible.
- Ensure signed URLs have sufficient TTL.

### “Failed to download image”
- Signed URL expired → request a fresh signed GET URL from Go backend.
- Object key mismatch → ensure Go backend signs keys belonging to the item/job.

---

## Where this is documented elsewhere
- System context and async flows: `docs/architecture.md`
- Full Go + AI contract examples: `docs/api/CONTRACT.md`
- DB schema for jobs/items/features: `docs/db/schema.md`
