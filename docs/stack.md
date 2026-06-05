# Tech Stack

## Backend
- **FastAPI** + Uvicorn — async API framework
- **SQLAlchemy 2.0** (async) — ORM
- **Alembic** — database migrations
- **Pydantic v2** — schema validation (bundled with FastAPI)
- **python-jose** + **passlib** — JWT authentication
- **httpx** — HTTP client for Efí API calls
- **BackgroundTasks** (FastAPI built-in) — non-blocking webhook processing

## Frontend
- **React** + **Vite** + **TypeScript**
- **TanStack Query** — server state and data fetching
- **React Router v6** — routing
- **Tailwind CSS** + **shadcn/ui** — styling and UI components
- **Zustand** — lightweight global state (auth session, etc.)
- **React Hook Form** + **Zod** — form handling and validation

## Database
- **PostgreSQL**

## Infrastructure
- **Docker Compose** — services: `api`, `frontend`, `db`, `nginx`
- **Nginx** — reverse proxy; serves React build and proxies to FastAPI
- **GitHub Actions** — CI (lint + tests on PR)
