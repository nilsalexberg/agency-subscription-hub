# Agency Subscription Hub

Admin panel for managing subscription plans, clients, and revenue splits. Integrates with Efí payment gateway for automated billing, webhook processing, and checkout link generation. Includes role-based access (admin/viewer), payment history, audit logs, and a dashboard with revenue metrics.

## Stack

**Backend:** FastAPI · SQLAlchemy 2.0 (async) · Alembic · Pydantic v2 · PostgreSQL  
**Frontend:** React · Vite · TypeScript · TanStack Query · Tailwind CSS · shadcn/ui · Zustand  
**Infra:** Docker Compose · Nginx · GitHub Actions

## Prerequisites

- Docker & Docker Compose
- Node.js + pnpm (for local frontend dev)
- Poetry (for local backend dev)

## Setup

1. Copy the example env file and fill in your values:

```bash
cp .env.example .env
```

Required variables:

| Variable | Description |
|---|---|
| `POSTGRES_USER` | Database user |
| `POSTGRES_PASSWORD` | Database password |
| `POSTGRES_DB` | Database name |
| `SECRET_KEY` | JWT signing secret |
| `EFI_CLIENT_ID` | Efí API client ID |
| `EFI_CLIENT_SECRET` | Efí API client secret |

2. Start services and run migrations:

```bash
make up
make migrate
```

## Development

Start backend + DB in Docker, frontend with hot reload:

```bash
make dev
```

- API: http://localhost:8000
- Frontend dev server: http://localhost:5173
- API docs: http://localhost:8000/docs

## Production

Build frontend and start all services via Nginx:

```bash
make prod
```

App served at http://localhost (port 80).

## Commands

| Command | Description |
|---|---|
| `make up` | Start all services (detached) |
| `make down` | Stop all services |
| `make dev` | Start services + frontend dev server |
| `make logs` | Tail service logs |
| `make migrate` | Run Alembic migrations |
| `make prod` | Build frontend + start production stack |

## Project Structure

```
├── backend/          # FastAPI app
│   ├── app/
│   │   ├── api/      # Route handlers
│   │   ├── core/     # Config, auth, dependencies
│   │   ├── models/   # SQLAlchemy models
│   │   ├── schemas/  # Pydantic schemas
│   │   └── services/ # Business logic, Efí integration
│   └── tests/
├── frontend/         # React app
│   └── src/
│       ├── api/      # API client functions
│       ├── components/
│       ├── pages/
│       └── store/    # Zustand stores
├── nginx/            # Nginx config
├── alembic/          # Migrations
└── docs/             # System description and stack docs
```

## Features

- **Plans** — CRUD; synced to Efí on create with stored Efí ID
- **Recipients** — CRUD; registered in Efí; participate in split configs
- **Split Configs** — percentage distribution among recipients (must total 100%)
- **Clients** — linked to a plan; checkout link auto-generated via Efí
- **Payments & Webhooks** — Efí handles recurring charges; events processed async
- **History** — payment history and admin audit log
- **Dashboard** — active/overdue/cancelled counts, monthly revenue, recent payments
- **Roles** — Admin (full access) and Viewer (read-only)
