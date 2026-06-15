# Schema-Driven Admin Panel

## Architecture

Generic CRUD layer driven by declarative configs. Each resource defined once (backend `ResourceConfig` + frontend `ResourceConfig`); router factory and generic React components handle the rest. Escape hatches allow per-resource overrides without abandoning the pattern.

Resources: Plans, Recipients, SplitConfigs, Clients, Payments (read-only), AuditLogs (read-only), Users. Dashboard and Settings are custom, outside the generic layer.

---

## Backend

### Contracts — `app/admin/contracts.py`

Pure type definitions. Exports:

- `ResourceConfig` — model class, read/write Pydantic schemas, URL prefix, optional `search_field`, optional `RelationLoadConfig` list, optional `OverrideMap`
- `RelationLoadConfig` — frozen dataclass: SQLAlchemy attribute name + display field serialized alongside FK in list responses
- `Operation` — literal type
- `OverrideMap` — alias; `None` key = factory default; callable = full replacement

### Router Factory — `app/admin/factory.py`

`build_router(config)` returns `APIRouter` with five CRUD routes. Checks `config.overrides` first; non-`None` callable replaces default handler.

Default handlers:
- async SQLAlchemy session via `DB` DI
- List: `skip`/`limit`, `ilike` search on `search_field`, safe sort (unknown `sort_by` falls back to PK), `func.count()` for total, `selectinload` per `RelationLoadConfig`, display field serialized as `{attribute}_{display_field}`
- Retrieve/update/delete: PK lookup via `sa_inspect` (no hardcoded `model.id`), 404 if missing
- Create/update: dynamic body type via `__annotations__["body"]` patch — `from __future__ import annotations` absent so FastAPI resolves patched type

Auth at route level: `Depends(get_current_user)` on list/retrieve; `Depends(require_admin)` on create/update/delete — enforced for override handlers too.

### Resource Registry — `app/resources.py`

`RESOURCE_CONFIGS` — 7 entries: Recipients, SplitConfigs, Plans, Clients, Payments, AuditLogs, Users.

`register_admin_resources(app)` iterates list, mounts each router under `/admin`. Called from `app/main.py` on startup.

Override rules:
- Payments, AuditLog: create/update/delete → `_method_not_allowed` (405)
- Users: create overridden (password-based creation stays in auth)
- Recipients, SplitConfigs, Plans, Clients: no write overrides

Schemas in `app/schemas/`: `plan`, `recipient`, `split_config`, `client`, `payment`, `audit_log`. `UserAdminWrite` in `schemas/user.py` (email + role + is_active, no password).

Relation display fields: Plans include `split_config_name`; Clients include `plan_name`.

---

## Frontend

### Types — `frontend/src/types/resource.ts`

`FieldDescriptor`: key, label, field type (`text | email | number | boolean | select | date | textarea | relation`), display flags (`showInList/Form/Detail`), validation flags (`required`, `readonly`), UX flags (`sortable`, `filterable`), optional `selectOptions`, optional `relation` (resource + labelField + valueField), escape hatches `renderCell` / `renderInput`.

`ResourceConfig`: key, label, pluralLabel, endpoint, `fields` array, `relatedLists` array (label + resource + foreignKey + fields), `extraActions` array (label + variant + action callback).

### Data Hook — `frontend/src/hooks/useResource.ts`

`useResource<T>(endpoint, options?)` — accepts endpoint + optional `{ listParams?, id? }`.

Returns `{ list, detail, create, update, remove }`:
- `list`, `detail`: `useQuery` (enabled only when respective option provided)
- `create`, `update`, `remove`: `useMutation`; success handlers call `queryClient.invalidateQueries`

`ListParams` (`page/pageSize/search/sortBy/sortOrder/filters`) mapped to backend params (`skip/limit/q/sort_by/sort_dir`). Backend `{ items, total }` unwrapped to `ListResult<T>` (`{ data, total, page, pageSize }`). Errors propagate as exceptions. `apiClient` handles auth headers and 401 logout.

### Components

**`ResourceList.tsx`** — accepts `ResourceConfig`, drives all state internally.
- List params in component state; passed to `useResource`
- Search debounced 300ms; rendered only when any field has `filterable: true`; resets page on change
- Columns from `fields` where `showInList: true`; sortable fields render toggle button with `SortIndicator`
- Relation values resolved from `{attribute}_{labelField}` key; `renderCell` takes priority
- Read-only detection: no Edit/Delete when no `showInForm` field exists
- Inline delete confirmation (no modal): sets `confirmDeleteId`, row shows Yes/No in-place
- Extra actions: 1–2 as inline buttons; 3+ in `ActionsDropdown` with click-outside listener
- Pagination: prev/next, rows-per-page select (10/20/50/100), X–Y of Z counter

**`ResourceForm.tsx`** — accepts `ResourceConfig` and `'create' | 'edit'`. Edit reads `:id` from URL, fetches record, populates via `reset()`.

Zod schema built dynamically: boolean → `z.boolean()`, number → `z.coerce.number()`, others → `z.string()` (`.min(1)` when `required`). Memoized. Wired via `zodResolver`.

Input dispatch: `boolean` → `Checkbox` via `Controller`; `textarea` → `Textarea`; `select` → native select; `relation` → `RelationSelect` via `Controller`; `number` → `Input type="number"`; others → `Input`. `readonly` → static text. `renderInput` replaces input entirely.

**`RelationSelect.tsx`** — controlled `Select` fetching related resource list (up to 100 rows); options as `{ labelField: valueField }`.

On submit: `create.mutateAsync` or `update.mutateAsync`, then navigate to `/${config.key}`. Mutation errors shown as inline alert.

**`ResourceDetail.tsx`** — reads `:id`, fetches record. Renders `showInDetail` fields as `<dl>` grid via `resolveCellValue` (respects `renderCell`). Header has Back + conditional Edit. One `RelatedList` per `relatedLists` entry — fetches up to 50 rows with FK filter, renders as embedded table.

**`Sidebar.tsx`** — accepts `resources: ResourceConfig[]`. One `NavLink` per resource using `pluralLabel` and `/${key}` with `end={false}`. Dashboard and Settings hardcoded outside resource loop.

### Resource Registry — `frontend/src/resources/`

Seven config files: `recipients.ts`, `split-configs.ts`, `plans.ts`, `clients.ts`, `payments.ts`, `audit-logs.ts`, `users.ts`. Each exports typed `ResourceConfig` with full fields, `relatedLists` (Plans → Clients, Clients → Payments), and `extraActions: []`.

`index.ts` exports `RESOURCES: ResourceConfig[]` in order: Recipients → SplitConfigs → Plans → Clients → Payments → AuditLogs → Users.

### Router — `router.tsx`

Routes generated from `RESOURCES`. Per resource: `/${key}` (list) + `/${key}/:id` (detail). Writable resources (any `showInForm: true` field) also get `/${key}/new` + `/${key}/:id/edit`. Read-only resources (Payments, AuditLogs) get list + detail only. `AppLayout` auth guard (redirect `/login` when no token) wraps all generated routes alongside `/dashboard` and `/settings`.

---

## Escape Hatches

**Backend** (`tests/test_escape_hatches.py`): override fully replaces default (DB untouched when override doesn't write); auth enforced regardless of override; `None` in override map falls back to factory default; domain-level create override can run custom logic + DB insert; override handlers can raise `HTTPException`.

**Frontend** (`src/components/admin/__tests__/`): `renderCell` takes priority over relation resolution, boolean rendering, raw value fallback; `renderInput` renders custom element, suppresses default input, receives `FieldDescriptor` + form methods, supports multiple independent overrides per form. Sidebar hardcoded entries coexist with 0–7 dynamic resource links.
