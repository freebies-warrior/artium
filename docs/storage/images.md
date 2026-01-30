# Image Uploading & Image Retrieval (Cloudflare R2)

This document explains how image uploading and image retrieval works in our backend using **Cloudflare R2** (S3-compatible) with a **private bucket**, and how the frontend/AI should use it.

This documentation reflects the current approach:
- Upload via presigned PUT URL (frontend/AI uploads directly to R2)
- Retrieval via signed GET URLs returned from item endpoints (backend signs keys stored in DB)

---

## Goals

- Avoid sending large image files through the backend server.
- Store images in a **private** R2 bucket (no public access required).
- Store **object keys** (not public URLs) in the database.
- Return **short-lived signed GET URLs** from item endpoints so the frontend/AI can display images.
- Avoid a generic “sign any key” endpoint which can be abused.

---

## Key Concepts

### Object Key

An object key is the identifier/path of an object inside the bucket.

Example key:
- uploads/<user_id>/20260130T120000Z-acde1234abcd5678.jpg

We store this key in the DB (currently some code may store it in a column named `url`, but the value is actually a key).

### Presigned URL

A presigned URL is a temporary URL that grants access to a private object without exposing storage credentials.

We use:
- Presigned PUT URL: for uploading bytes directly to R2
- Presigned GET URL: for viewing/downloading bytes directly from R2

Presigned URLs expire (for example: 10–15 minutes).

---

## Why We Store Object Keys Instead of Public URLs

Storing keys is better because:
- We can change domains/CDN later without migrating DB rows.
- We keep the bucket private while still enabling viewing via signed URLs.
- We avoid leaking permanent public links.
- We reduce security risk: the backend only signs URLs for objects it knows belong to items.

---

## High-Level Flow

### Upload Flow (Frontend/AI → R2)

1. Frontend/AI requests “upload instructions” from backend (presigned PUT URL).
2. Backend responds with:
   - key: object key where the file should live
   - upload_url: presigned PUT URL
3. Frontend/AI uploads the file directly to R2 using HTTP PUT to upload_url.
4. Frontend/AI calls item creation/update endpoint with picture_keys (the keys returned from presign).

### Frontend View Flow (Frontend ← Backend ← R2)

1. Frontend requests items from the backend (list or detail).
2. Backend loads picture keys from DB for those items.
3. Backend generates signed GET URLs for those keys.
4. Backend returns the item response with pictures[].url set to the signed GET URLs.
5. Frontend displays images with standard image tags using the signed URLs.

---

## Backend Endpoints

### 1) POST /uploads/presign

Purpose:
- Generate a presigned PUT URL for uploading an image to R2.
- Return an object key which will later be stored in DB for item pictures.

Auth:
- Protected (requires user auth) so uploads are associated with a user.

Request JSON example:

    {
      "filename": "example.jpg",
      "content_type": "image/jpeg"
    }

Response JSON example:

    {
      "key": "uploads/<uid>/20260130T120000Z-acde1234abcd5678.jpg",
      "upload_url": "https://<accountid>.r2.cloudflarestorage.com/<bucket>/uploads/...?...signature..."
    }

Notes:
- upload_url expires (example: 10 minutes).
- Backend validates content_type starts with "image/".

### 2) PUT <upload_url> (Direct-to-R2)

Purpose:
- Upload the image bytes directly to R2 (no backend file streaming).

Frontend/AI does:
- Method: PUT
- Body: raw file bytes
- Header: Content-Type must match the content_type used for presigning

Conceptual example:
- PUT upload_url
- Header: Content-Type: image/jpeg
- Body: <file_bytes>

### 3) Item endpoints return signed image URLs

We do NOT use a generic endpoint like:
- GET /uploads/presign-get?key=...

Instead, we sign image URLs inside item endpoints so the backend can enforce permissions safely.

Endpoints:
- GET /items
  - Returns list of items
  - Attaches 0–1 picture per item for list view (thumbnail/cover)
  - Signs those picture URLs before responding

- GET /items/:id
  - Returns one item with full details
  - Attaches all pictures for the item
  - Signs all picture URLs before responding

Typical response shape example (fields may vary by your current schema):

    {
      "id": "....",
      "title": "....",
      "pictures": [
        {
          "id": "....",
          "url": "https://<accountid>.r2.cloudflarestorage.com/<bucket>/uploads/...?...signed...",
          "item_id": "...."
        }
      ]
    }

Implementation detail:
- In DB, the picture record stores the object key (for example in pictures.url).
- Before returning JSON, the backend replaces pictures[].url with a signed GET URL.

---

## How Signing Works

Where signing happens:
- When getting an Item: after loading all pictures (keys) for that item, sign that item’s pictures

Expiry behavior:
- Signed GET URLs expire (example: 15 minutes).

---

## Database Storage

What we store:
- Object keys, not public URLs.

Example DB value:
- uploads/<uid>/20260130T120000Z-acde1234abcd5678.jpg

---

## Frontend Usage

### Uploading an image

1. User selects a file.
2. Frontend calls POST /uploads/presign with filename and content_type.
3. Frontend receives key and upload_url.
4. Frontend uploads file bytes using PUT upload_url.
5. Frontend stores key and later sends it to item creation/update as picture_keys.

### Creating an item with pictures

Frontend calls POST /items.

Request includes picture keys:

    {
      "title": "Example",
      "base_price": 10000,
      "increment": 500,
      "time_start": "2026-02-01T10:00:00Z",
      "time_end": "2026-02-03T10:00:00Z",
      "picture_keys": [
        "uploads/<uid>/...jpg",
        "uploads/<uid>/...png"
      ]
    }

Backend inserts:
- item record
- picture records containing those keys

### Displaying images

Frontend calls:
- GET /items (list view) or GET /items/:id (detail view)

Backend returns pictures[].url as signed GET URLs.

Frontend renders:
- img tag with src equal to the returned signed url

Because the signed URL contains authorization in the query parameters, no special headers are needed for an img tag.

---

## Cloudflare R2 Configuration

Backend environment variables:
- R2_ACCOUNT_ID
- R2_ACCESS_KEY_ID
- R2_SECRET_ACCESS_KEY
- R2_BUCKET

AWS SDK usage:
- We use the AWS S3-compatible SDK to connect to R2 (Cloudflare).
- Endpoint format: https://<accountid>.r2.cloudflarestorage.com
- Region: auto
- Path-style addressing enabled (UsePathStyle = true)

---

## CORS Notes (Important for Browser Upload)

Because the browser uploads directly to R2 with PUT, the R2 bucket must allow CORS for your frontend origins, for example:
- http://localhost:3000
- your deployed frontend domain

Minimum CORS allowances:
- Methods: PUT, GET, HEAD (and usually OPTIONS)
- Headers: Content-Type

If CORS is not configured, the browser PUT will fail even with a valid presigned URL.
