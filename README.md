# Artium — AI-Assisted Art Auctions
Auction-first art marketplace with AI features that help buyers understand listings, preview artworks in their space, and discover similar items.

> Hackathon project (PINUS Hack 2026). Built in 7 days by a 5-person team.

<!-- 📽️ Demo video: TODO  
🌐 Live demo: TODO  
📄 Pitch deck: TODO -->

---

## Tracks (Hackathon)
- **Primary:** Track 4 — Virtual Viewing & Decision Support  
- **Secondary:** Track 3 — Collector Discovery & Personalisation

---

## What Artium Does
### Auction (core)
- Browse auction listings
- View listing details (images, attributes, current bid)
- Place bids + view bid history

### AI Support (buyer-focused)
- **Preview in your room:** upload a room photo → generate a preview mockup + short description  
  - Includes quality checks and fallback if the photo is unsuitable.
- **Auto-extract artwork details:** extract key attributes from the artwork image (editable tags)
- **Similar items:** recommend visually similar works for discovery  
  - Includes “why similar” evidence (shared tags/palette/style similarity)

---

## Architecture (High-level)
**Next.js (web)** → **Go API** → **Postgres**  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;↘︎ Object Storage (temporary image uploads)  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;↘︎ AI pipelines (preview, extraction, similarity)

More details: [`docs/architecture.md`](docs/architecture.md)

---

## Repo Structure
```
.
├── apps
│   ├── backend
│   └── frontend
├── docs
│   ├── api
│   │   └── CONTRACT.md
│   ├── architecture.md
│   └── db
│       └── schema.md
├── LICENSE
└── README.md
```

---

## Setup

### Database

#### Running Postgres via Docker

1. Install Docker and Docker Compose
2. From the repo root, run:
   ```bash
   docker compose up -d
   ```
3. The Postgres DB will be available at `localhost:5432` with:
    - User: `postgres`
    - Password: `postgres`
    - DB: `artium`
4. To stop the DB:
    ```bash
    docker compose stop
    ```

#### Resetting the DB

To reset the database (drops all data and recreates tables):
```bash
cd apps/backend
go run ./apps/backend/cmd/dbreset  # Make sure Go is installed
```

---

## Docs
- Architecture: [docs/architecture.md](docs/architecture.md)
- API contract: [docs/api/CONTRACT.md](docs/api/CONTRACT.md)
- DB schema: [docs/db/schema.md](docs/db/schema.md)

---

## Progress
See [docs/progress.md](docs/progress.md)

---

## Team
- Ferdinand Halim Santoso (@ferdihs)
- Andrew Daniel Janong (@andrewjanong)
- Ryan Justyn (@rjustyn1)
- Fredy Lawrence (@chrainx)
- Angky Akdi Frandy Putrakelana (@angkyakdifp)
