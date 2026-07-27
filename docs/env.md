# Environment Reference

This document is the source of truth for environment variable naming across Artium apps.

## Rollout note

Deployed environment sources must switch from `AI_SERVICE_TOKEN` to `INTERNAL_TOKEN` before the backend code change ships. The backend now reads `INTERNAL_TOKEN` only.

## Backend

| Variable | Status | Notes |
| --- | --- | --- |
| `DATABASE_URL` | Required | Postgres connection string for the Go API. |
| `JWT_SECRET` | Required | Required by backend auth and frontend auth route verification. |
| `INTERNAL_TOKEN` | Required | Shared internal secret for trusted backend-to-agents callbacks. |
| `APP_BASE_URL` | Required | Public app URL used in backend-generated links. |
| `BACKEND_BASE_URL` | Required | Backend base URL used by backend-generated links. |
| `AI_BASE_URL` | Required | Base URL for the AI service consumed by the backend. |
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

| Variable | Status | Notes |
| --- | --- | --- |
| `BACKEND_URL` | Required | Server-side base URL for frontend route handlers talking to the backend. |
| `JWT_SECRET` | Required | Required for the frontend auth route. |

## Agents

| Variable | Status | Notes |
| --- | --- | --- |
| `BACKEND_URL` | Required | Base URL for agents calling backend internal endpoints. |
| `INTERNAL_TOKEN` | Required | Shared internal secret used on trusted agent callbacks. |
| `VECTORDB_CONFIG` | Required | Path to the agents vector DB config file. |
| `PINECONE_API_KEY` | Required | Pinecone API key for retrieval/indexing flows. |
| `OPENAI_API_KEY` | Required | OpenAI API key for agents that call OpenAI-compatible APIs. |
| `OPENAI_BASE_URL` | Optional | Override for OpenAI-compatible base URL. |
| `SERPAPI_API_KEY` | Required | Search provider key for feature extraction lookups. |
| `APP_ENV` | Optional | Runtime environment name. |
| `LOG_LEVEL` | Optional | Log level override. |
| `VISUALIZER_USE_LANGGRAPH` | Optional | Toggle for the LangGraph visualizer path. |
| `VISUALIZER_GEMINI_MODEL` | Optional | Image-capable Gemini model selection. |
| `VISUALIZER_GEMINI_TEXT_MODEL` | Optional | Text Gemini model selection. |
| `VISUALIZER_MAX_RETRIES` | Optional | Retry count for visualizer runs. |
| `VISUALIZER_ENHANCE_IF_LOW_QUALITY` | Optional | Enables enhancement pass on low-quality outputs. |
| `MANUS_API_KEY` | Feature-gated | Required only when Manus-backed feature text is enabled. |
