# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development

```bash
make dev          # Docker (backend + DB) + frontend hot reload at localhost:5173
make up           # Docker all services detached
make down         # Stop all services
make logs         # Tail service logs
make migrate      # Run Alembic migrations (requires running containers)
make migration m="description"  # Autogenerate new migration
make prod         # Build frontend + start production stack via Nginx on port 80
```

### Backend (run from `backend/`)

```bash
poetry run pytest                         # All tests
poetry run pytest tests/test_auth.py      # Single test file
poetry run pytest -k "test_name"          # Single test by name
poetry run ruff check .                   # Lint
poetry run ruff format .                  # Format
```

### Frontend (run from `frontend/`)

```bash
pnpm run dev      # Dev server
pnpm run test     # Vitest run (once)
pnpm run test:watch
pnpm run lint
pnpm run build
```

## Architecture

### Schema-driven admin panel

Both backend and frontend use a declarative config-per-resource pattern — one declaration drives routes, ORM queries, and UI simultaneously.

**Backend** (`backend/app/resources.py` → `backend/app/admin/`):
- `ResourceConfig` (`admin/contracts.py`) declares model, read/write schemas, URL prefix, optional search field, eager-loaded relations, and per-operation overrides.
- `build_router(config)` (`admin/factory.py`) generates five standard CRUD routes (list/retrieve/create/update/delete) from one config. Auth is always enforced. Handler type annotations are patched at runtime so FastAPI resolves the correct Pydantic body schema.
- `RESOURCE_CONFIGS` in `resources.py` is the single source of truth. All configs are mounted under `/api/admin`.
- Read-only resources use a shared `_READ_ONLY_OVERRIDES` map returning 405.
- Do **not** add `from __future__ import annotations` to `factory.py` — it breaks the runtime annotation patching.

**Frontend** (`frontend/src/resources/`, `frontend/src/types/resource.ts`):
- `ResourceConfig` (TypeScript) declares `key`, `endpoint`, `fields` (with per-field `showInList`/`showInForm`/`showInDetail`/`type`/`sortable`/`filterable`), `relatedLists`, and `extraActions`.
- `RESOURCES` array (`resources/index.ts`) is consumed by `router.tsx` to generate routes automatically — `ResourceList`, `ResourceDetail`, `ResourceForm` components render any resource generically.
- `relation` field type triggers `RelationSelect` which fetches from another resource endpoint.
- List responses from the backend include `{relation}_{displayField}` keys (e.g. `plan_name`) for FK label display without a second round-trip.

Adding a new resource requires:
1. SQLAlchemy model + Alembic migration
2. Pydantic read/write schemas
3. Entry in `RESOURCE_CONFIGS` (`backend/app/resources.py`)
4. `ResourceConfig` file in `frontend/src/resources/` + export from `resources/index.ts`

### Auth

JWT-based. `POST /auth/login` returns a bearer token. `get_current_user` dep validates token; `require_admin` dep additionally checks `Role.ADMIN`. The `DB` type alias (`Annotated[AsyncSession, Depends(get_db)]`) is used throughout route handlers.

### Efí integration

`backend/app/integrations/efi/client.py` — async httpx client with automatic token refresh. `get_efi_client()` is `@lru_cache` singleton. Sandbox vs production controlled by `EFI_SANDBOX` env var. Webhook flow: POST receives opaque token → `fetch_notification(token)` resolves events via GET.

### Testing

Backend tests use SQLite in-memory via `conftest.py` — no running DB needed. `override_db` fixture is `autouse=True`, replacing the PostgreSQL session for all tests. `SECRET_KEY`, `DATABASE_URL`, and Efí credentials are set as env vars in `conftest.py`.

## Commit convention

Format: `<type>: <subject>` — no scope, no long body.
