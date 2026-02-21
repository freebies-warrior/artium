# Go Backend API Contract

This document is the **human-readable API contract** that the Go backend provides.

- **Base URL (local):** `http://localhost:8080`
- **Content-Type:** `application/json`
- **Auth:** Bearer token (JWT) for protected endpoints

> Source of truth (for now): this file.  
> When endpoints change, update this contract immediately.

---

## Conventions

### Authentication

Protected endpoints require:

- `Authorization: Bearer <token>`

If missing/invalid:

- `401 Unauthorized`

### Standard Error Format

All error responses SHOULD follow:

```json
{
  "error": {
    "code": "STRING_CODE",
    "message": "Human readable message",
    "details": {}
  }
}
```

Common error codes:

- `VALIDATION_ERROR`
- `UNAUTHORIZED`
- `FORBIDDEN`
- `NOT_FOUND`
- `CONFLICT`
- `INTERNAL_ERROR`
- `AI_REJECTED_INPUT`

### IDs and timestamps

- `id` fields: UUID strings
- timestamps: ISO-8601 in UTC (e.g., `"2026-01-27T13:22:10Z"`)

### Money

All money values are **integers in SGD dollars** (not cents).
For example:

- `1500` means **$1500.00**
- `10500` means **$10,500.00**

---

## Entities (Response Shapes)

### User (public)

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "username": "user_123",
  "verified": false
}
```

### Picture

```json
{
  "id": "uuid",
  "item_id": "uuid",
  "key": "some-key",
  "created_at": "2026-01-27T13:22:10Z"
}
```

### Item (Listing)

```json
{
  "id": "uuid",
  "seller_id": "uuid",
  "title": "Sunset on Canvas",
  "description": "A warm, calm landscape...",
  "author": "Unknown",
  "features": {
    "medium": "oil",
    "subject": ["landscape"],
    "style": "impressionist-ish",
    "palette": ["#2f3a4c", "#d9c7a6"],
    "orientation": "landscape",
    "mood": ["calm", "warm"],
    "confidence": {
      "medium": 0.84,
      "style": 0.62
    },
    "source": "ai+user_edit"
  },
  "base_price": 10000,
  "increment": 500,
  "status": "active",
  "time_start": "2026-01-27T10:00:00Z",
  "time_end": "2026-01-28T10:00:00Z",
  "created_at": "2026-01-27T09:00:00Z",
  "updated_at": "2026-01-27T09:05:00Z",
  "pictures": [
    {
      "id": "uuid",
      "item_id": "uuid",
      "key": "https://.../image.jpg",
      "created_at": "2026-01-27T09:00:10Z"
    }
  ]
}
```

### Bid

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "item_id": "uuid",
  "price": 10500,
  "timestamp": "2026-01-27T13:22:10Z"
}
```

### Visualization Job

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "item_id": "uuid",
  "room_image_key": "rooms/<uid>/20260131T120000Z-acde1234abcd5678.jpg",
  "status": "queued",
  "result_image_key": null,
  "result_description": null,
  "error_message": null,
  "created_at": "2026-01-31T12:00:00Z",
  "updated_at": "2026-01-31T12:00:00Z"
}
```

---

## Auth Endpoints

## Sign Up

Create a new user account.

- **Method:** `POST`
- **Path:** `/auth/signup`
- **Auth:** none

### Request

```json
{
  "email": "user@example.com",
  "username": "user_123",
  "password": "plain-text-password"
}
```

### Response `201`

```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "user_123",
    "verified": false
  }
}
```

### Errors

- `400 VALIDATION_ERROR` (invalid email/password)
- `409 CONFLICT` (email/username already exists)

---

## Login

Authenticate and receive a token.

- **Method:** `POST`
- **Path:** `/auth/login`
- **Auth:** none

### Request

```json
{
  "email": "user@example.com",
  "password": "plain-text-password"
}
```

### Response `200`

```json
{
  "token": "jwt-token-string",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "user_123",
    "verified": false
  }
}
```

### Errors

- `400 VALIDATION_ERROR`
- `401 UNAUTHORIZED` (wrong credentials)
- `403 FORBIDDEN` (credentials correct but `verified=false`, return “Please verify your email”)

---

## Verify Email

Verify an account using a token (single-use, expiring).  
On success, sets `users.verified = true`.

- **Method:** `POST`
- **Path:** `/auth/verify`
- **Auth:** none

### Request

```json
{
  "token": "verification-token-from-email-link"
}
```

### Response `200`

```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "user_123",
    "verified": true
  }
}
```

### Errors

- `400 VALIDATION_ERROR` (missing token, invalid token, expired token, already used token)
- `500 INTERNAL_ERROR` (database / unexpected)

---

## Resend Verification Email

Request a new verification link if the user is not verified.  
This endpoint should not leak whether the email exists.

- **Method:** `POST`
- **Path:** `/auth/resend-verification`
- **Auth:** none

### Request

```json
{
  "email": "user@example.com"
}
```

### Response `200`

```json
{
  "ok": true
}
```

### Errors

- `400 VALIDATION_ERROR` (invalid email format)
- `500 INTERNAL_ERROR` (unexpected / database)

---

## Item Endpoints

## List Items

Returns auction items for browsing (max 100 items).

- **Method:** `GET`
- **Path:** `/items`
- **Auth:** none
- **Notes:** default max = 100; support pagination via `limit` and `cursor`.

### Query Params

- `limit` (optional, int, default 20, max 100)
- `cursor` (optional, string)
- `status` (optional, string: `draft|active|ended|cancelled`)
- `seller_id` (optional, uuid)
- `q` (optional, string search on title/author)

### Response `200`

```json
{
  "items": [
    {
      "id": "uuid",
      "seller_id": "uuid",
      "seller_username": "seller_123",
      "title": "Sunset on Canvas",
      "author": "Unknown",
      "status": "active",
      "year_created": 1995,
      "height": 60.0,
      "width": 80.0,
      "base_price": 10000,
      "increment": 500,
      "time_start": "2026-01-27T10:00:00Z",
      "time_end": "2026-01-28T10:00:00Z",
      "highest_bid_id": "uuid",
      "highest_bid_amount": 10500,
      "highest_bidder_id": "uuid",
      "highest_bid_time": "2026-01-27T13:22:10Z",
      "pictures": [
        {
          "id": "uuid",
          "item_id": "uuid",
          "key": "some-key",
          "created_at": "2026-01-27T09:00:10Z"
        }
      ]
    }
  ],
  "next_cursor": "opaque-string-or-null"
}
```

### Errors

- `400 VALIDATION_ERROR`

---

## Get Item Info

Returns item details + pictures + current bid state (if you compute it).

- **Method:** `GET`
- **Path:** `/items/{item_id}`
- **Auth:** none

### Response `200`

```json
{
  "item": {
    "id": "uuid",
    "seller_id": "uuid",
    "seller_username": "seller_123",
    "title": "Sunset on Canvas",
    "description": "A warm, calm landscape...",
    "author": "Unknown",
    "features": { "medium": "oil" },
    "year_created": 1995,
    "height": 60.0,
    "width": 80.0,
    "base_price": 10000,
    "increment": 500,
    "status": "active",
    "time_start": "2026-01-27T10:00:00Z",
    "time_end": "2026-01-28T10:00:00Z",
    "highest_bid_id": "uuid",
    "highest_bid_amount": 10500,
    "highest_bidder_id": "uuid",
    "highest_bid_time": "2026-01-27T13:22:10Z",
    "features": {
      "vision_brushstroke": {},
      "vision_blending": {},
      "vision_physicality": {},
    },
    "pictures": [
      {
        "id": "uuid",
        "item_id": "uuid",
        "key": "some-key",
        "created_at": "2026-01-27T09:00:10Z"
      }
    ]
  }
}
```

### Errors

- `404 NOT_FOUND`

---

## Post Item

Create a new auction item. Seller supplies basic info + image URLs (uploaded separately).

- **Method:** `POST`
- **Path:** `/items`
- **Auth:** required

### Request

```json
{
  "title": "Sunset on Canvas",
  "description": "A warm, calm landscape...",
  "author": "Unknown",
  "base_price": 10000,
  "increment": 500,
  "year_created": 1995,
  "height": 60.0,
  "width": 80.0,
  "time_start": "2026-01-27T10:00:00Z",
  "time_end": "2026-01-28T10:00:00Z",
  "picture_keys": ["some-key-1", "some-key-2"]
}
```

### Response `201`

```json
{
  "item": {
    "id": "uuid",
    "seller_id": "uuid",
    "seller_username": "seller_123",
    "title": "Sunset on Canvas",
    "description": "A warm, calm landscape...",
    "author": "Unknown",
    "base_price": 10000,
    "increment": 500,
    "year_created": 1995,
    "height": 60.0,
    "width": 80.0,
    "status": "draft",
    "time_start": "2026-01-27T10:00:00Z",
    "time_end": "2026-01-28T10:00:00Z",
    "highest_bid_id": "uuid",
    "highest_bid_amount": null,
    "highest_bidder_id": null,
    "highest_bid_time": null,
    "features": {},
    "pictures": [
      {
        "id": "uuid",
        "item_id": "uuid",
        "key": "some-key-1",
        "created_at": "2026-01-27T09:00:10Z"
      }, {
        "id": "uuid",
        "item_id": "uuid",
        "key": "some-key-2",
        "created_at": "2026-01-27T09:00:10Z"
      }
    ]
  }
}
```

### Errors

- `400 VALIDATION_ERROR`
- `401 UNAUTHORIZED`

---

## Upload Endpoints

## Get Presigned Upload Link

- **Method:** `POST`
- **Path:** `/uploads/presign`
- **Auth:** required

### Request

```json
{
  "filename": "example.jpg",
  "content_type": "image/jpeg"
}
```

### Response `200`

```json
{
  "key": "uploads/<uid>/20260130T120000Z-acde1234abcd5678.jpg",
  "upload_url": "https://<accountid>.r2.cloudflarestorage.com/<bucket>/uploads/...?...signature...",
  "view_url": "https://<accountid>.r2.cloudflarestorage.com/<bucket>/uploads/...?...signature..."
}
```

### Errors

- `400 VALIDATION_ERROR` (invalid file type)
- `500 INTERNAL_ERROR`

### Notes

Purpose:
- Generate a presigned PUT URL for uploading an image to R2.
- Generate a presigned GET URL for preview as well
- Return an object key which will later be stored in DB for item pictures.

Auth:
- Protected (requires user auth) so uploads are associated with a user.

Notes:
- upload_url and view_url expires (example: 10 minutes).
- Backend validates content_type starts with "image/".

---

## Bid Endpoints

## Place Bid

Place a bid for an item.

- **Method:** `POST`
- **Path:** `/items/{item_id}/bids`
- **Auth:** required

### Request

```json
{
  "price": 10500
}
```

### Response `201`

```json
{
  "bid": {
    "id": "uuid",
    "user_id": "uuid",
    "item_id": "uuid",
    "price": 10500,
    "timestamp": "2026-01-27T13:22:10Z"
  }
}
```

### Errors

- `400 VALIDATION_ERROR` (invalid price format)
- `401 UNAUTHORIZED`
- `404 NOT_FOUND` (item not found)
- `409 CONFLICT` (bid too low / auction not active / auction ended)

### Notes

Server enforces:

- item is `active`
- now is within `[time_start, time_end]`
- `price >= current_price + increment` (or `>= base_price` if no bids)

---

## Get Bid History

Fetch recent bids for an item.

- **Method:** `GET`
- **Path:** `/items/{item_id}/bids`
- **Auth:** none

### Query Params

- `limit` (optional, int, default 20, max 100)

### Response `200`

```json
{
  "bids": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "item_id": "uuid",
      "price": 10500,
      "timestamp": "2026-01-27T13:22:10Z"
    }
  ]
}
```

### Errors

- `404 NOT_FOUND`

---

## Users Endpoints

---

## List Users

---

Returns all users (public-safe fields only).

- **Method:** `GET`
- **Path:** `/users`
- **Auth:** none

**Query Parameters**
- `limit` (optional, int)
  - Default: `20`
  - Max: `100`
- `q` (optional, string)
  - Username search (case-insensitive, partial match).
  - Example: `q=fer` matches usernames containing `fer`.
- `cursor` (optional, string)
  - Cursor-based pagination token returned by this endpoint (`next_cursor`).
  - Opaque to clients (do not try to parse/modify).

### Response (200)
```json
{
  "data": [
    {
      "id": "uuid-string",
      "username": "string",
      "created_at": "RFC3339 timestamp"
    }
  ],
  "next_cursor": "string-or-null"
}
```

### Errors
- `400 VALIDATION_ERROR` if `limit` is not a valid integer.
- `400 VALIDATION_ERROR` if query params are invalid (e.g., malformed cursor).

### Notes
- Results are sorted by `created_at` descending, then `id` descending.
- If there are more results, `next_cursor` will be returned. Pass it into the next request as `cursor`.
- If there are no more results, `next_cursor` will be `null`.

### Examples
- First page:
  - `GET /users?limit=20`
- Search by username:
  - `GET /users?q=fer&limit=20`
- Next page:
  - `GET /users?limit=20&cursor=<next_cursor_from_previous_response>`

---

## AI Endpoints (Visualizer)

> Note: Visualizer is **asynchronous**. The frontend creates a job, then polls for status/result.

---

## Create Visualizer Job (Preview in Room)

Create a new visualization job to merge an item image with a room photo.

- **Method:** `POST`
- **Path:** `/visualizations`
- **Auth:** required

### Request

```json
{
  "item_id": "uuid",
  "item_image_key": "items/<uid>/20260131T120000Z-acde1234abcd5678.jpg",
  "room_image_key": "rooms/<uid>/20260131T120000Z-acde1234abcd5678.jpg",
  "item_dimensions": {
    "width_cm": 60,
    "height_cm": 40
  }
}
```

### Response `201`

```json
{
  "job": {
    "id": "uuid",
    "user_id": "uuid",
    "item_id": "uuid",
    "item_image_key": "items/<uid>/20260131T120000Z-acde1234abcd5678.jpg",
    "room_image_key": "rooms/<uid>/20260131T120000Z-acde1234abcd5678.jpg",
    "status": "queued",
    "result_image_key": null,
    "result_description": null,
    "error_message": null,
    "created_at": "2026-01-31T12:00:00Z",
    "updated_at": "2026-01-31T12:00:00Z"
  }
}
```

### Errors

- `400 VALIDATION_ERROR` (missing/invalid `item_id`, missing/invalid `room_image_key`)
- `401 UNAUTHORIZED`
- `403 FORBIDDEN` (user not allowed to preview this item)
- `404 NOT_FOUND` (item not found)
- `409 CONFLICT` (item has no image / item not eligible)

### Notes

- `room_image_key` is obtained by uploading a room photo to R2 via `/uploads/presign`.
- Do not send arbitrary external URLs to the AI service; pass **keys**.

---

## Get Visualizer Job Status

Fetch job state and (if completed) the output.

- **Method:** `GET`
- **Path:** `/visualizations/{job_id}`
- **Auth:** required

### Response `200` (queued / processing)

```json
{
  "job": {
    "id": "uuid",
    "user_id": "uuid",
    "item_id": "uuid",
    "item_image_key": "items/<uid>/20260131T120000Z-acde1234abcd5678.jpg",
    "room_image_key": "rooms/<uid>/20260131T120000Z-acde1234abcd5678.jpg",
    "status": "processing",
    "result_image_key": null,
    "result_description": null,
    "error_message": null,
    "created_at": "2026-01-31T12:00:00Z",
    "updated_at": "2026-01-31T12:01:10Z"
  }
}
```

### Response `200` (succeeded)

```json
{
  "job": {
    "id": "uuid",
    "user_id": "uuid",
    "item_id": "uuid",
    "item_image_key": "items/<uid>/20260131T120000Z-acde1234abcd5678.jpg",
    "room_image_key": "rooms/<uid>/20260131T120000Z-acde1234abcd5678.jpg",
    "status": "succeeded",
    "result_image_key": "visualizations/<job_id>/result.jpg",
    "result_image_url": "https://.../visualizations/<job_id>/result.jpg",
    "result_description": "A warm-toned landscape piece displayed above a modern sofa...",
    "error_message": null,
    "created_at": "2026-01-31T12:00:00Z",
    "updated_at": "2026-01-31T12:02:30Z"
  }
}
```

### Response `200` (failed)

```json
{
  "job": {
    "id": "uuid",
    "user_id": "uuid",
    "item_id": "uuid",
    "item_image_key": "items/<uid>/20260131T120000Z-acde1234abcd5678.jpg",
    "room_image_key": "rooms/<uid>/20260131T120000Z-acde1234abcd5678.jpg",
    "status": "failed",
    "result_image_key": null,
    "result_description": null,
    "error_message": "Unable to process images",
    "created_at": "2026-01-31T12:00:00Z",
    "updated_at": "2026-01-31T12:02:30Z"
  }
}
```

### Errors

- `401 UNAUTHORIZED`
- `403 FORBIDDEN`
- `404 NOT_FOUND` (job not found)

---

## List Visualizer Jobs (Optional)

List visualizer jobs for the current user (useful for UI history).

- **Method:** `GET`
- **Path:** `/visualizations`
- **Auth:** required

### Query Params

- `limit` (optional, int, default 20, max 100)
- `cursor` (optional, string)
- `item_id` (optional, uuid)

### Response `200`

```json
{
  "jobs": [
    {
      "id": "uuid",
      "item_id": "uuid",
      "status": "succeeded",
      "result_image_key": "visualizations/<job_id>/result.jpg",
      "result_description": "..."
    }
  ],
  "next_cursor": "opaque-string-or-null"
}
```

### Errors

- `400 VALIDATION_ERROR`
- `401 UNAUTHORIZED`

## Update Visualizer Job
(Update is internal only; frontend cannot call this.)

- **Method:** `PUT`
- **Path:** `/visualizations/{job_id}`
- **Auth:** internal only

### Request

```json
{
  "status": "succeeded",
  "result_description": "A warm-toned landscape piece displayed above a modern sofa...",
  "error_message": null
}
```

### Response (200)

```json
{
  "ok": true
}
```

### Errors

- `400 VALIDATION_ERROR`
- `404 NOT_FOUND`

### Notes

- Used by AI backend to update job status/results.
- Only `status`, `result_description`, and `error_message` can be updated.

---

## Get Similar Items

Recommend similar items based on the clicked item (ignore price range).

- **Method:** `GET`
- **Path:** `/ai/similarItems`
- **Auth:** none

### Query Params

- `item_id` (required, uuid)
- `limit` (optional, int, default 8, max 24)

### Response `200`

```json
{
  "item_id": "uuid",
  "results": [
    {
      "item": {
        "id": "uuid",
        "title": "Another Landscape",
        "author": "Unknown",
        "status": "active",
        "pictures": [
          {
            "id": "uuid",
            "item_id": "uuid",
            "key": "https://.../thumb.jpg",
            "created_at": "2026-01-27T09:00:10Z"
          }
        ]
      },
      "similarity": {
        "score": 0.83,
        "reasons": [
          "Similar color palette (warm tones)",
          "Similar subject (landscape)",
          "Similar composition (horizon placement)"
        ],
        "shared_tags": ["landscape", "warm", "oil"]
      }
    }
  ]
}
```

### Errors

- `400 VALIDATION_ERROR`
- `404 NOT_FOUND`

---

## AI Feature Extractor Endpoints

## Update Item Features (Internal Only)

Update an item’s `features` column after AI extraction.

- Method: PUT
- Path: `/items/{item_id}/features`
- Auth: internal only

Request:

    {
      "features": features_json
    }

Response 200:

    { "ok": true }

Errors:
- 400 VALIDATION_ERROR (invalid item_id, missing/invalid `features`)
- 401 UNAUTHORIZED (missing/invalid internal token)
- 404 NOT_FOUND (item not found)
- 500 INTERNAL_ERROR

Notes:
- This endpoint overwrites `items.features` with the provided JSON object.
- Keep error messages short and do not include secrets, tokens, or presigned URLs.

---

## Frontend Page → Endpoint Mapping (MVP)

### Auth page

- `POST /auth/signup`
- `POST /auth/login`

### Home page

- `GET /items` (browse items)
- `POST /items` (seller posts item for auction)

### Item page

- `GET /items/{item_id}` (item details)
- `POST /items/{item_id}/bids` (place bid)
- `GET /items/{item_id}/bids` (bid history)
- `POST /ai/preview-in-room` (generate combined image)
- `GET /ai/similar?item_id=...` (similar items)
- `POST /uploads/presign` (upload room photo to R2)
- `POST /visualizations` (create async visualizer job)
- `GET /visualizations/{job_id}` (poll status + fetch result)

---

# AI Backend API Contract

This document is the **human-readable API contract** that the AI microservice provides.

---

## AI Visualizer Endpoints

---

## Visualize in Room

---

Start a visualization job to merge an artwork image with a room photo.

- **Method:** `POST`
- **Path:** `/agents/visualizer/visualize_installation`
- **Auth:** Internal Only
- **Header:**
  - `X-Internal-Token`: `<secret>`

### Request

```json
{
  "room_url": "https://.../rooms/<uid>/20260131T120000Z-acde1234abcd5678.jpg",
  "art_url": "https://.../items/<item_id>/main.jpg",
  "upload_image_url": "https://.../visualizations/<job_id>/result.jpg",
  "result_image_key": "visualizations/<job_id>/result.jpg",
  "item_dimensions": {
    "width": 60,
    "height": 40
  },
  "job_id": "uuid",
}
```

### Response `200`

```json
{
  "ok": true
}
```

### Errors
- `400 VALIDATION_ERROR` (missing/invalid fields)
- `500 INTERNAL_ERROR` (unexpected / processing failure)

### Notes
- `room_url` and `art_url` are presigned GET URLs to R2 objects.
- The AI service downloads the images, processes them, and uploads the result back to R2.
- The AI service does **not** return the result directly; it updates the job state in the Go backend via DB or another mechanism.

---

## AI Feature Extractor Endpoints

## Extract Item Features

Start feature extraction for an item using its images.

- **Method**: POST
- **Path**: `/agents/feature_extractor/extract`
- **Auth**: Internal Only
- **Header**:
  - `X-Internal-Token`: `<secret>`

Request (example):
```json
    {
      "item_id": "uuid",
      "image_keys": [
        "uploads/<uid>/20260130T120000Z-acde1234abcd5678.jpg",
        "uploads/<uid>/20260130T120000Z-acde1234abcd9999.jpg"
      ],
      "image_get_urls": [
        "https://<accountid>.r2.cloudflarestorage.com/<bucket>/uploads/...?...signature...",
        "https://<accountid>.r2.cloudflarestorage.com/<bucket>/uploads/...?...signature..."
      ],
      "callback_url": "https://<go-backend>/internal/items/<item_id>/features",
      "metadata" : {
        "author"  : "artwork-author", // can be [null]
        "title"   : "artwork-title", // can be [null]
        "year"    : "artwork-year-created" //can be [null]
      }
    }
```

Response 200:

    { "ok": true }

Errors:
- 400 VALIDATION_ERROR (missing/invalid fields, empty image list, non-image URLs)
- 500 INTERNAL_ERROR

Notes:
- `image_get_urls` are presigned GET URLs generated by the Go backend.
- The AI worker should download images using `image_get_urls`, then call `callback_url` once features are extracted.
