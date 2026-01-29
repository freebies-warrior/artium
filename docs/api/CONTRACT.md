# API Contract

This document is the **human-readable API contract** between the Next.js frontend and the Go backend.

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
      "url": "https://.../image.jpg",
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
    "pictures": [
      {
        "id": "uuid",
        "item_id": "uuid",
        "url": "some-key-1",
        "created_at": "2026-01-27T09:00:10Z"
      }, {
        "id": "uuid",
        "item_id": "uuid",
        "url": "some-key-2",
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

## AI Endpoints (Buyer Support)

> Note: These are **support features** for buyer experience. They do not alter auction outcomes directly.

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
            "url": "https://.../thumb.jpg",
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

## Preview Artwork in a Room (Generate / Compose)

Generate a preview image showing the artwork placed in the user's room.

- **Method:** `POST`
- **Path:** `/ai/preview-in-room`
- **Auth:** required (or none for demo)

### Request

```json
{
  "room_image_url": "https://.../room.jpg",
  "item_id": "uuid"
}
```

### Response `200`

```json
{
  "preview_image_url": "https://.../preview.jpg",
  "description": "A warm-toned landscape piece that complements neutral interiors...",
  "notes": [
    "Preview is not scale-accurate (no AR sizing).",
    "Lighting and color may vary from real life."
  ],
  "quality": {
    "accepted": true,
    "checks": {
      "brightness_ok": true,
      "blur_ok": true,
      "wall_detected": true
    }
  }
}
```

### Errors

- `400 VALIDATION_ERROR`
- `422 AI_REJECTED_INPUT` (image too dark/blur/no wall detected and no manual box)
- `500 INTERNAL_ERROR`

---

## Frontend Page → Endpoint Mapping (MVP)

### Login page

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

---
