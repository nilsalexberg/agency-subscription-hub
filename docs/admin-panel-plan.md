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

### Step 3 — Build the central backend resource registry

Single file (`app/resources.py`) imports all models and schemas, defines resource config list, iterates it to register each router on the FastAPI app. `app/main.py` calls this registration function.

No router setup lives outside these two files. Custom endpoints not covered by the factory (e.g., checkout-link generation) are imported separately and mounted alongside the generated router under the same prefix.

### Step 4 — Handle relation-aware list responses

Use Option A: factory accepts optional relation load configs (model attribute name + display field name). Generated list handler uses `selectinload` for those relationships and serializes the display field alongside the FK. Keeps network round-trips minimal and frontend config simple.

### Step 5 — Apply auth and permission middleware

Generated routes must pass through existing JWT auth dependency and role-based access control. Apply correct `dependencies` at router level — no generated route should be accidentally public. Distinguish admin-only routes (create, update, delete) from viewer-accessible routes (list, retrieve).

---

## Phase 2 — Frontend: TypeScript Types

### Step 6 — Define the field descriptor type

```typescript
interface FieldDescriptor {
  key: string;
  label: string;
  type: 'text' | 'email' | 'number' | 'boolean' | 'select' | 'date' | 'textarea' | 'relation';
  showInList: boolean;
  showInForm: boolean;
  showInDetail: boolean;
  required: boolean;
  sortable: boolean;
  filterable: boolean;
  readonly: boolean;
  selectOptions?: { label: string; value: string | number }[];
  relation?: {
    resource: string;
    labelField: string;
    valueField: string;
  };
  renderCell?: (record: unknown) => React.ReactNode;
  renderInput?: (field: FieldDescriptor, form: unknown) => React.ReactNode;
}
```

### Step 7 — Define the resource config type

```typescript
interface ResourceConfig {
  key: string;
  label: string;
  pluralLabel: string;
  endpoint: string;
  fields: FieldDescriptor[];
  relatedLists: {
    label: string;
    resource: string;
    foreignKey: string;
    fields: FieldDescriptor[];
  }[];
  extraActions: {
    label: string;
    variant: string;
    action: (record: unknown) => void;
  }[];
}
```

---

## Phase 3 — Frontend: Shared Data Hook

### Step 8 — Implement the useResource hook

Single hook used by all three views. Wraps TanStack Query, accepts resource endpoint string, exposes:
- `list(params)` — paginated fetch with sort, search, filter; returns `{ data, total, page, pageSize }`
- `getOne(id)` — fetch single record
- `create(payload)` — POST + invalidate list cache
- `update(id, payload)` — PUT + invalidate list and detail caches
- `remove(id)` — DELETE + invalidate list cache

Mutations use `useMutation`; reads use `useQuery`. Network errors surface as thrown exceptions. Single point of contact with the API for all generic views.

---

## Phase 4 — Frontend: Generic Components

### Step 9 — Implement the List view component

Accepts resource config, uses `useResource` internally. Columns derived from fields where `showInList` is true. Relation fields render resolved label (from Step 4), not raw FK. Fields with `renderCell` overrides use the override function.

Renders:
- Debounced search input (only if any field has `filterable: true`)
- Sortable column headers (toggle sort direction, re-fetch)
- Pagination controls (prev/next, page size selector)
- Per-row: Edit button (navigate to form), Delete button (inline confirm → remove mutation), extra actions (dropdown if more than two)

Deletion uses inline "confirm?" state on the button row — no modal.

### Step 10 — Implement the Form component

Handles create and edit via `mode` prop. Edit mode receives record id and fetches existing record to pre-populate.

Input type auto-selected from field `type`:
- `text`, `email`, `number`, `date` → matching HTML input
- `textarea` → Textarea component
- `boolean` → Checkbox component
- `select` → Select component with `selectOptions`
- `relation` → async Select: fetches target resource list on mount, maps to `{ label, value }` pairs

`readonly` fields render as read-only text in all modes. `renderInput` overrides replace the input entirely.

Validation: React Hook Form + Zod. Schema derived dynamically from field descriptors — required fields get `.min(1)`/`.nonempty()`, numbers get `z.number()`, booleans get `z.boolean()`, others get `z.string()`.

On success: navigate back to list. On error: display inline messages.

### Step 11 — Implement the Detail view component

Fetches one record via `getOne`. Renders fields where `showInDetail: true` as a read-only labeled key-value grid. `renderCell` overrides apply to value display.

Below the grid: one section per `relatedLists` entry, each rendered as an embedded table filtered by current record id. Related lists fetch up to 50 rows (not paginated). Each uses `useResource` with FK filter as query param.

Edit button in header navigates to edit form.

### Step 12 — Implement the Shell/layout component

Sidebar with one entry per resource, ordered by config array. Each entry shows `pluralLabel`. Clicking navigates to list view.

Route structure per resource (React Router v6 nested):
- `/<resource-key>` → List
- `/<resource-key>/new` → Form (create)
- `/<resource-key>/:id` → Detail
- `/<resource-key>/:id/edit` → Form (edit)

Top bar: app title, logged-in user, logout button. Shell wraps all three generic views and passes correct resource config based on current route.

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
