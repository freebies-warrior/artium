# Environment Reference

This document is the source of truth for environment variable naming across Artium apps.

## Rollout note

Deployed environment sources must switch from `AI_SERVICE_TOKEN` to `INTERNAL_TOKEN` before the backend code change ships. The backend now reads `INTERNAL_TOKEN` only.

## Deployment locations

- Frontend preview and production env vars live in Vercel project settings. Update them through Vercel so the deployment history is the audit trail.
- Backend and agents production env vars live on the VM used by `.github/workflows/deploy.yml`, in `~/artium/apps/backend/.env` and `~/artium/apps/agents/.env`, which are consumed by `~/artium/docker-compose.prod.yml`. There is no separate backend/agents staging environment in this repo. Update those VM env files in the same operational change that ships the code, and use the GitHub Actions run log plus the PR/commit history as the audit trail.
- When a variable name changes, update this document first, then update the relevant deployment source before shipping the code that depends on it.

## Secret rotation record

Any secret change must be recorded in the PR that makes the change. Use one record per rotation and list every deployment source touched by that rotation:

| Field | Required value |
| --- | --- |
| Operator | Person who made the change |
| Timestamp (UTC) | When the change was applied |
| Environment | `preview`, `production`, or `none` |
| Affected deployment sources | `Vercel project settings (frontend preview/production)`, `~/artium/apps/backend/.env`, `~/artium/apps/agents/.env` |
| Variables rotated | Secret names only, never values |
| Deployment run | Vercel deployment URL or GitHub Actions run URL |
| Verification | Short note describing the post-deploy check |

For `JWT_SECRET`, include both the frontend Vercel source and the backend VM source in the same record. For backend and agents, use `none` for staging because there is no separate staging environment in this repo.

## Backend

| Variable | Status | Notes |
| --- | --- | --- |
| `DATABASE_URL` | Required | Postgres connection string for the Go API. |
| `JWT_SECRET` | Required | Shared with the frontend auth route; use one value in both places. |
| `INTERNAL_TOKEN` | Required | Shared internal secret for trusted backend-to-agents callbacks. |
| `APP_BASE_URL` | Optional | Public app URL used in backend-generated links. Defaults to `http://localhost:3000` in code. |
| `BACKEND_BASE_URL` | Optional | Backend base URL used by backend-generated links. Defaults to `http://localhost:8080` in code. |
| `AI_BASE_URL` | Optional | Base URL for the AI service consumed by the backend. Defaults to `http://localhost:8000` in code. |
| `CORS_ALLOWED_ORIGINS` | Optional | Comma-separated allowed origins for local/dev access control. |
| `ITEM_STATUS_SWEEPER_INTERVAL` | Optional | Background sweeper interval. Defaults in code. |
| `R2_ACCOUNT_ID` | Required | Cloudflare R2 account ID. |
| `R2_ACCESS_KEY_ID` | Required | Cloudflare R2 access key. |
| `R2_SECRET_ACCESS_KEY` | Required | Cloudflare R2 secret key. |
| `R2_BUCKET` | Required | Bucket used for uploads and generated assets. |
| `SMTP_HOST` | Required | SMTP host for transactional email. |
| `SMTP_PORT` | Required | SMTP port for transactional email. |
| `SMTP_USERNAME` | Optional | SMTP username when auth is enabled. |
| `SMTP_PASSWORD` | Optional | SMTP password when auth is enabled. |
| `EMAIL_FROM_NAME` | Required | Sender display name. |
| `EMAIL_FROM_ADDRESS` | Required | Sender email address. |

## Frontend server routes

These variables are for Next.js server routes only. Do not expose the backend base URL to the browser.
`JWT_SECRET` is a shared value with the backend; rotations must be recorded once and include both deployment sources.

| Variable | Status | Notes |
| --- | --- | --- |
| `BACKEND_URL` | Required | Server-side base URL for frontend route handlers talking to the backend. |
| `JWT_SECRET` | Required | Shared with backend auth; use one value in both places. |

## Agents

| Variable | Status | Notes |
| --- | --- | --- |
| `BACKEND_URL` | Optional | Base URL for agents calling backend internal endpoints. Defaults to `http://localhost:8080` in code. |
| `INTERNAL_TOKEN` | Required | Shared internal secret used on trusted agent callbacks. |
| `GOOGLE_API_KEY` | Required | Gemini API key used by the visualizer and feature extractor at startup. |
| `VECTORDB_CONFIG` | Optional | Path to the agents vector DB config file. Defaults to `RAG/config.yaml` in code. |
| `PINECONE_API_KEY` | Required | Pinecone API key for retrieval/indexing flows. |
| `OPENAI_API_KEY` | Required | OpenAI API key for agents that call OpenAI-compatible APIs. |
| `OPENAI_BASE_URL` | Optional | Override for OpenAI-compatible base URL. |
| `SERPAPI_API_KEY` | Required | Search provider key for feature extraction lookups. |
| `APP_ENV` | Optional | Runtime environment name. |
| `LOG_LEVEL` | Optional | Log level override. |
| `VISUALIZER_GEMINI_MODEL` | Optional | Image-capable Gemini model selection. |
| `VISUALIZER_GEMINI_TEXT_MODEL` | Optional | Text Gemini model selection. |
| `VISUALIZER_MAX_RETRIES` | Optional | Retry count for visualizer runs. |
| `VISUALIZER_ENHANCE_IF_LOW_QUALITY` | Optional | Enables enhancement pass on low-quality outputs. |
| `MANUS_API_KEY` | Feature-gated | Required only when Manus-backed feature text is enabled. |
