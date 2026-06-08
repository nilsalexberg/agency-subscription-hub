# UI Components

All components live in `src/components/ui/` and export from `src/components/ui/index.ts`.

Import: `import { Button, Card, Badge } from '@/components/ui'`

---

## Design Tokens

Defined in `src/index.css` via Tailwind v4 `@theme`. Key CSS variables:

| Token | Value | Usage |
|---|---|---|
| `--color-bg` | `#F7F6F3` | Page background |
| `--color-surface` | `#FFFFFF` | Cards, inputs |
| `--color-surface-raised` | `#F2F1EE` | Hover states, disabled |
| `--color-border` | `#E3E2DD` | All borders |
| `--color-fg` | `#1A1916` | Primary text |
| `--color-fg-secondary` | `#57564F` | Secondary text |
| `--color-fg-muted` | `#93928B` | Placeholders, hints |
| `--color-primary` | `#2563EB` | Primary actions |
| `--color-danger` | `#DC2626` | Errors, destructive |
| `--color-success` | `#16A34A` | Success states |
| `--color-warning` | `#D97706` | Warning states |

Fonts: `Manrope` (body, `font-sans`), `Syne` (display headings, `font-display`).

---

## Button

```tsx
<Button>Save</Button>
<Button variant="secondary">Cancel</Button>
<Button variant="destructive">Delete</Button>
<Button variant="outline">Export</Button>
<Button variant="ghost">Dismiss</Button>
<Button variant="link">View details</Button>
<Button size="sm">Small</Button>
<Button size="lg">Large</Button>
<Button size="icon"><PlusIcon /></Button>
<Button disabled>Disabled</Button>
```

**Variants:** `primary` (default) · `secondary` · `destructive` · `outline` · `ghost` · `link`  
**Sizes:** `sm` · `md` (default) · `lg` · `icon` · `icon-sm`

---

## Input

```tsx
<Input placeholder="Enter value" />
<Input type="email" placeholder="Email" />
<Input error />
<Input disabled />
```

Pass `error={true}` to show red border + focus ring. Pairs with `FormField` for full form rows.

---

## Textarea

```tsx
<Textarea placeholder="Notes..." rows={4} />
<Textarea error />
```

Same API as `Input`. Resizable vertically by default.

---

## Select

```tsx
<Select>
  <option value="">Choose...</option>
  <option value="active">Active</option>
  <option value="cancelled">Cancelled</option>
</Select>
<Select error />
```

Native `<select>` with custom chevron icon and matching Input styling.

---

## Label

```tsx
<Label htmlFor="email">Email</Label>
<Label required>Plan name</Label>
```

Pass `required` to render a red asterisk.

---

## FormField

Composes label + input + hint/error message into a single block.

```tsx
<FormField label="Email" required htmlFor="email" hint="Used for billing notifications">
  <Input id="email" type="email" />
</FormField>

<FormField label="Plan name" error="Name is required" htmlFor="plan-name">
  <Input id="plan-name" error />
</FormField>
```

---

## Card

```tsx
<Card>
  <CardHeader>
    <CardTitle>Active Clients</CardTitle>
    <CardDescription>Subscriptions in good standing</CardDescription>
  </CardHeader>
  <CardContent>
    <p>42</p>
  </CardContent>
  <CardFooter>
    <Button variant="ghost" size="sm">View all</Button>
  </CardFooter>
</Card>
```

**Sub-components:** `Card` · `CardHeader` · `CardTitle` · `CardDescription` · `CardContent` · `CardFooter`

---

## Badge

```tsx
<Badge>Default</Badge>
<Badge variant="success">Active</Badge>
<Badge variant="warning">Overdue</Badge>
<Badge variant="danger">Cancelled</Badge>
<Badge variant="info">Processing</Badge>
<Badge variant="primary">New</Badge>
```

**Variants:** `default` · `primary` · `success` · `warning` · `danger` · `info`

---

## Alert

```tsx
<Alert title="Payment failed">Retry or contact support.</Alert>
<Alert variant="success" title="Subscription created">Client notified via email.</Alert>
<Alert variant="warning">Auto-cancellation scheduled in 3 days.</Alert>
<Alert variant="danger" title="Webhook error">Last 3 events failed to process.</Alert>
<Alert variant="info">Efí credentials not configured yet.</Alert>
```

**Variants:** `default` · `info` · `success` · `warning` · `danger`  
Each variant renders the matching Lucide icon automatically.

---

## Spinner

```tsx
<Spinner />
<Spinner size="sm" />
<Spinner size="lg" />
<Spinner className="text-white" />
```

**Sizes:** `sm` · `md` (default) · `lg`  
Color inherits from `currentColor` — override with `text-*` class.

---

## Checkbox

```tsx
<Checkbox />
<Checkbox checked onChange={...} />
<Checkbox disabled />
```

Native checkbox styled with `accent-color` set to primary blue.

---

## Separator

```tsx
<Separator />
<Separator orientation="vertical" className="h-6" />
```

**Orientations:** `horizontal` (default, full width) · `vertical` (requires explicit height)

---

## Table

```tsx
<Table>
  <TableHeader>
    <TableRow>
      <TableHead>Client</TableHead>
      <TableHead>Plan</TableHead>
      <TableHead>Status</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    <TableRow>
      <TableCell>Acme Corp</TableCell>
      <TableCell>Pro</TableCell>
      <TableCell><Badge variant="success">Active</Badge></TableCell>
    </TableRow>
  </TableBody>
</Table>
```

**Sub-components:** `Table` · `TableHeader` · `TableBody` · `TableRow` · `TableHead` · `TableCell`  
Wraps in an overflow container automatically.
