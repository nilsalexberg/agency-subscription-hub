# Schema-Driven Admin Panel — Implementation Plan

## Overview

Generic CRUD layer driven by declarative configs. No existing per-resource pages or endpoints — frontend pages are stubs and backend has only auth/users. Each resource is defined once (backend config + frontend config); the router factory and generic React components handle the rest. Escape hatches allow surgical overrides without abandoning the pattern.

Targets: Plans, Recipients, Split Configs, Clients, Payments (read-only), History (read-only), Users. Dashboard and Settings are custom and stay outside the generic layer.

---

## Phase 1 — Backend: Router Factory

### ~~Step 1 — Define the resource registration contract~~ ✅

`app/admin/contracts.py` — pure type definitions, no implementation. Exports `ResourceConfig` (model class, read/write Pydantic schemas, URL prefix, optional search field, optional `RelationLoadConfig` list, optional `OverrideMap`), `RelationLoadConfig` (frozen dataclass: SQLAlchemy attribute name + display field to serialize alongside FK in list responses), `Operation` literal, and `OverrideMap` alias. `None`/absent override key = use factory default; non-`None` callable = full replacement.

### ~~Step 2 — Implement the router factory function~~ ✅

`app/admin/factory.py` — `build_router(config)` returns `APIRouter` with five CRUD routes. Each operation checks `config.overrides` first; a non-`None` callable replaces the default handler.

Default handlers: async SQLAlchemy session via `DB` DI. List uses `skip`/`limit`, `ilike` search on `search_field`, safe sort (unknown `sort_by` falls back to PK), separate `func.count()` query for total, `selectinload` for each `RelationLoadConfig` with display field serialized as `{attribute}_{display_field}` key. Retrieve/update/delete look up by PK via `sa_inspect` (no hardcoded `model.id`), return 404 if missing. Create/update accept dynamic body type via post-definition `__annotations__["body"] = write_schema` patch — `from __future__ import annotations` intentionally absent so FastAPI resolves the patched type correctly.

Auth applied at route level: `Depends(get_current_user)` on list/retrieve, `Depends(require_admin)` on create/update/delete — enforced even for override handlers.

### ~~Step 3 — Build the central backend resource registry~~ ✅

`app/resources.py` defines `RESOURCE_CONFIGS` (7 entries: Recipients, SplitConfigs, Plans, Clients, Payments, AuditLogs, Users) and `register_admin_resources(app)`, which iterates the list and mounts each generated router under `/admin`. `app/main.py` calls this on startup.

Read-only resources (Payments, AuditLog) override create/update/delete with `_method_not_allowed` → 405. Users override create only (password-based creation stays in auth). Writable resources (Recipients, SplitConfigs, Plans, Clients) have no write overrides. Plans and Clients declare `RelationLoadConfig` for FK display fields (split_config name, plan name).

Pydantic schemas added in `app/schemas/`: `plan`, `recipient`, `split_config`, `client`, `payment`, `audit_log`. `UserAdminWrite` added to `schemas/user.py` (email + role + is_active, no password). Tested in `tests/test_resources.py`: registry structure, all 7 list routes return 401 (not 404), read-only 405 enforcement, user create 405, read-only list still returns 200.

### ~~Step 4 — Handle relation-aware list responses~~ ✅

Implemented in factory (Step 2): `RelationLoadConfig` list in `ResourceConfig`, `selectinload` per relation, display field serialized as `{attribute}_{display_field}` key alongside FK. Plans include `split_config_name`; Clients include `plan_name`.

### ~~Step 5 — Apply auth and permission middleware~~ ✅

Implemented in factory (Step 2): `Depends(get_current_user)` on list/retrieve routes; `Depends(require_admin)` on create/update/delete routes. Applied via `dependencies=[...]` at route registration — enforced even for override handlers.

---

## Phase 2 — Frontend: TypeScript Types

### ~~Step 6 — Define the field descriptor type~~ ✅

`frontend/src/types/resource.ts` exports `FieldDescriptor`: key, label, field type union (`text | email | number | boolean | select | date | textarea | relation`), display flags (`showInList/Form/Detail`), validation flags (`required`, `readonly`), UX flags (`sortable`, `filterable`), optional `selectOptions`, optional `relation` (resource + labelField + valueField), and escape hatches `renderCell` / `renderInput`.

### ~~Step 7 — Define the resource config type~~ ✅

`frontend/src/types/resource.ts` exports `ResourceConfig`: key, label, pluralLabel, endpoint, `fields` array of `FieldDescriptor`, `relatedLists` array (label + resource + foreignKey + fields), and `extraActions` array (label + variant + action callback).

---

## Phase 3 — Frontend: Shared Data Hook

### ~~Step 8 — Implement the useResource hook~~ ✅

`frontend/src/hooks/useResource.ts` — `useResource<T>(endpoint, options?)` accepts endpoint string and optional `{ listParams?, id? }`. Returns `{ list, detail, create, update, remove }`.

`list` and `detail` are `useQuery` results (enabled only when their respective option is provided). `create`, `update`, `remove` are `useMutation` instances. All three mutation success handlers call `queryClient.invalidateQueries` to keep caches in sync — `update` and `remove` also invalidate the detail cache.

Internal fetch functions map `ListParams` (`page/pageSize/search/sortBy/sortOrder/filters`) to backend params (`skip/limit/q/sort_by/sort_dir`). Backend response shape `{ items, total }` is unwrapped into `ListResult<T>` (`{ data, total, page, pageSize }`). Errors propagate as thrown exceptions — no silent failures. `apiClient` from `api/client.ts` handles auth headers and 401 logout.

---

## Phase 4 — Frontend: Generic Components

### ~~Step 9 — Implement the List view component~~ ✅

`frontend/src/components/admin/ResourceList.tsx` — `ResourceList({ config })` accepts `ResourceConfig`, drives all state internally.

- List params (`page`, `pageSize`, `search`, `sortBy`, `sortOrder`) held in component state; passed to `useResource` as `listParams`.
- Search input debounced 300 ms via inline `useDebounce`; rendered only when any field has `filterable: true`. Resets page on change.
- Column headers from `fields` where `showInList: true`. Sortable fields render a `<button>` with `SortIndicator` (chevron icons); clicking toggles direction or switches column.
- Relation cell values resolved by reading `{attribute}_{labelField}` key from the record (attribute = `field.key` with `_id` suffix stripped). Falls back to raw value. `renderCell` override takes priority over all resolution logic.
- Read-only detection: resources with no `showInForm` field (Payments, AuditLog) get no Edit/Delete buttons.
- Inline delete confirmation: clicking trash sets `confirmDeleteId`; row shows "Delete? Yes / No" in-place. No modal.
- Extra actions: 1–2 render as inline `Button`s; 3+ render in `ActionsDropdown` (self-contained sub-component with per-instance open state and click-outside listener).
- Pagination: prev/next buttons, rows-per-page `Select` (10/20/50/100), "X–Y of Z" counter.
- Loading state: full-width centered `Spinner`. Error state: inline danger alert with message.

### ~~Step 10 — Implement the Form component~~ ✅

`frontend/src/components/admin/ResourceForm.tsx` — `ResourceForm({ config, mode })` accepts `ResourceConfig` and `'create' | 'edit'`. Edit mode reads `:id` from URL params via `useParams`, fetches the record with `useResource`, and populates the form via `reset()` on load.

Zod schema built dynamically in `buildZodSchema`: boolean fields → `z.boolean()`, number fields → `z.coerce.number()`, all others → `z.string()` (with `.min(1, 'Required')` when `required: true`). Schema is memoized. React Hook Form wired via `zodResolver`.

Input rendering dispatches on `field.type`: `boolean` → `Checkbox` via `Controller`; `textarea` → `Textarea`; `select` → native `Select` with `selectOptions`; `relation` → `RelationSelect` (see below) via `Controller`; `number` → `Input type="number"`; all others → `Input` with matching HTML type. `readonly` fields render as static text. `renderInput` escape hatch replaces the input entirely when set.

`frontend/src/components/admin/RelationSelect.tsx` — controlled `Select` that calls `useResource` to fetch the related resource list (up to 100 rows), renders options as `{ labelField: valueField }` pairs, shows "Loading…" while fetching.

On submit: `create.mutateAsync` or `update.mutateAsync` then navigate to `/${config.key}`. Mutation errors shown via inline `Alert`. Loading/error states for the detail fetch handled before rendering the form.

### ~~Step 11 — Implement the Detail view component~~ ✅

`frontend/src/components/admin/ResourceDetail.tsx` — `ResourceDetail({ config })` reads `:id` from URL params, fetches record via `useResource`. Renders `showInDetail` fields as a `<dl>` key-value grid using `resolveCellValue` (respects `renderCell` overrides). Header has Back button and conditional Edit button (only when any field has `showInForm`). Below grid: one `RelatedList` sub-component per `relatedLists` entry — fetches up to 50 rows via `useResource` with FK filter passed as `filters` query param, renders as embedded table using the relation's own `fields`. Loading/error states handled for both main record and each related list independently.

### ~~Step 12 — Implement the Shell/layout component~~ ✅

`src/components/layout/Sidebar.tsx` updated to accept `resources: ResourceConfig[]` prop. Renders one `NavLink` per resource using `pluralLabel` and `/${key}`, with `end={false}` so nested routes (`/new`, `/:id`, `/:id/edit`) keep the entry active. Dashboard and Settings remain as custom hardcoded entries outside the resource loop. Duplicated `className` logic extracted to `linkClass` helper. `src/components/layout/AppLayout.tsx` imports `RESOURCES` from `src/resources/index.ts` and passes it to `Sidebar`. `src/components/layout/Header.tsx` updated to render "Admin Panel" title in the top-left per spec. `src/resources/index.ts` created as empty `RESOURCES: ResourceConfig[]` array — Step 13 populates it with actual configs, Step 14 uses it to generate routes in `router.tsx`.

---

## Phase 5 — Frontend: Resource Registry

### Step 13 — Build the central frontend resource registry

`src/resources/index.ts` exports ordered array of all resource configs. Each resource config defined in its own file under `src/resources/` (e.g., `src/resources/clients.ts`), imported and assembled into the array.

Shell reads array to build sidebar. Router reads array to generate routes. No resource-specific logic in shell or router. Custom pages (Dashboard, Settings) registered outside this array as standalone routes.

---

## Phase 6 — Wiring and Integration

### Step 14 — Connect the shell router to the app router

Replace stub per-resource route definitions in `router.tsx` with routes generated from resource config array. Shell wraps all admin routes. Existing auth guard (redirect to login if unauthenticated) still wraps the shell.

Verify custom routes (dashboard, settings) continue functioning alongside generated routes.

### Step 15 — Implement each resource

For each resource:
1. Write backend model, Pydantic schemas, and config entry (prefix, search field, overrides).
2. Write frontend resource config (fields, relations, related lists, extra actions).
3. Delete stub page components and let the generic shell handle routing.
4. Test list, create, edit, detail, and delete flows manually.

Order (least to most complex): Recipients → Split Configs → Plans → Clients → Users.

Payments and History are read-only: no `showInForm` fields, no create/edit/delete routes in factory (override map stubs them as 405), list views have search and filter but no action buttons.

### Step 16 — Verify escape hatches end-to-end

Test per-field `renderCell` and `renderInput` overrides in list and form components. Test that a backend override handler fully replaces the default (e.g., Client create calls Efí for checkout link instead of generic insert). Confirm a fully custom page can coexist with generated resources in the sidebar.

---

## Phase 7 — Quality Checks

### Step 17 — Type safety audit

Resource config types must be strict enough that wrong field type or missing required property is a TypeScript compile error. Hook return types must be correct. All generic components typed against resource config interface, not `any`.

### Step 18 — Permissions audit

Walk every generated backend route. Confirm admin-only operations (create, update, delete) reject Viewer-role tokens with 403. Confirm Viewer tokens access list and retrieve. Test explicitly — factory generates routes programmatically and a missing dependency could silently create open endpoints.

### Step 19 — Manual smoke test

For each resource: list loads, search filters, sort works, create validates and submits, edit pre-populates and updates, detail shows related lists, delete with confirmation removes record. No console errors, no broken API calls.
