# Features

## Plans
- CRUD; each plan synced to Efí on create (Efí ID stored locally)
- Linked to a split config
- Deactivation blocks new clients; existing subscriptions unaffected

## Recipients
- CRUD; each recipient registered in Efí on create
- Can participate in multiple split configs

## Split Configs
- Define percentage distribution among recipients
- Total must equal exactly 100% (enforced on save)
- One config can be reused across multiple plans

## Clients
- CRUD; linked to a plan on create
- Checkout link auto-generated via Efí on create
- Subscription statuses: Active / Overdue / Cancelled
- Manual cancellation by admin

## Payments & Webhook
- First payment via checkout link; Efí handles all subsequent charges
- Webhook endpoint receives Efí events: payment confirmed, payment failed, subscription cancelled
- Events processed async via FastAPI BackgroundTasks
- All events logged to history

## History
- Payment history: date, amount, status, transaction ID, client, plan
- Audit log: user actions (create/edit/delete on any entity), auto-cancellations

## Users & Roles
- **Admin** — full access: create, edit, delete any entity
- **Viewer** — read-only access across all modules

## Dashboard
- Active / overdue / cancelled client counts
- Current month revenue
- Recent payments feed
- Webhook error alerts

## General Settings (admin only)
- Days until auto-cancellation (default: 30)
- Efí API credentials (encrypted at rest)
- Webhook URL registered in Efí
