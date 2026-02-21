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
- [Background execution model](#background-execution-model)
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

**POST** `/agents/feature_extractor/extract`  
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
- Validation rules:
  - `item_id` is required and must be a valid UUID.
  - `image_keys` must be non-empty.
  - `image_get_urls` must be non-empty.
  - `len(image_keys)` must equal `len(image_get_urls)`.
  - `callback_url` remains optional for compatibility.

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

Python target for `apps/agents`: **3.12** (matches `pyproject.toml` and CI).

### Option A: `uv` (recommended)
```bash
cd apps/agents
uv sync --frozen --dev

# Run dev server (adjust module path if your app entrypoint differs)
uv run uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Quality checks (CI parity)
```bash
cd apps/agents
uv sync --frozen --dev
uv run ruff format --check .
uv run ruff check .
uv run pytest -q
```

### RAG tooling entrypoints
RAG provider logic lives under `agents/providers/rag`, while operational entrypoints live under `scripts/`.

```bash
cd apps/agents
uv run python -m scripts.rag_ingest --help
uv run uvicorn scripts.rag_api:app --host 0.0.0.0 --port 8010
```

### Option B: Docker (recommended for parity)
If your repo provides a Dockerfile for agents:
```bash
docker build -t artium-agents .
docker run --rm -p 8000:8000 --env-file .env artium-agents
```

### Environment variables
Copy the template first:

```bash
cd apps/agents
cp .env.example .env
```

| Variable | Required | Used by | Notes |
|---|---|---|---|
| `INTERNAL_TOKEN` | Yes (API service) | FastAPI auth + internal callbacks | Missing token returns `500 INTERNAL_TOKEN is not configured` on protected routes. |
| `BACKEND_URL` | Yes (API service) | Callback/update endpoints | Defaults to `http://localhost:8080`. |
| `LOG_LEVEL` | Optional | Shared logging | Defaults to `INFO`. |
| `GOOGLE_API_KEY` | Yes for visualizer/feature extraction | Gemini clients | Missing key raises clear startup/runtime config errors. |
| `SERPAPI_API_KEY` | Optional | Feature extractor market search | Required only when SerpAPI enrichment runs. |
| `OPENAI_API_KEY` | Yes for RAG/valuation flows | RAG scripts + valuation tooling | Required for text embeddings in RAG flows. |
| `PINECONE_API_KEY` | Yes for RAG/valuation flows | RAG scripts + valuation tooling | Required for Pinecone index/query access. |
| `MANUS_API_KEY` | Optional | RAG canonicalization | Required only when `feature_text.manus.enabled=true`. |
| `VECTORDB_CONFIG` | Optional | RAG scripts/providers | Defaults to `agents/providers/rag/config.yaml` (legacy fallback supported). |

Use `apps/agents/.env.example` as the source of truth for all currently supported settings.

---

## Project structure

The codebase is being migrated incrementally to a clearer package layout while keeping existing entrypoints stable.

### Target structure (WIP)
- `agents/core/` — orchestration, prompting, parsing, and other pure domain logic.
- `agents/providers/` — integration boundaries (LLM, HTTP, storage, and external clients).
- `agents/tasks/<task_name>/` — task-specific pipelines/services (for example, visualizer).
- `agents/utils/` — shared utilities used across tasks.

### Migration strategy
- Migrate one task at a time into `agents/tasks/...` to keep changes reviewable and low risk.
- Keep service boundaries selective: add `service.py` only when API code would otherwise depend on task-private internals.
- RAG entrypoints use a clean cutover: run `scripts.rag_api` and `scripts.rag_ingest` (no legacy `agents.providers.rag.*` module wrappers).

## Background execution model

Current async execution in the API uses FastAPI in-process `BackgroundTasks`.
This is temporary and intended for low-complexity local/early environments.

Future Iteration:
- move long-running jobs to a dedicated queue/worker model
- keep API handlers as thin enqueue + acknowledgement endpoints
- keep callback/result persistence behavior compatible with current flows

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

### “... is not configured”
- Ensure the missing variable exists in `apps/agents/.env` (copy from `.env.example`).
- Verify you are running commands from `apps/agents` so the resolved env file is used.
- For RAG flows, confirm `OPENAI_API_KEY` and `PINECONE_API_KEY` are both set.

---

## Where this is documented elsewhere
- System context and async flows: `docs/architecture.md`
- Full Go + AI contract examples: `docs/api/CONTRACT.md`
- DB schema for jobs/items/features: `docs/db/schema.md`
