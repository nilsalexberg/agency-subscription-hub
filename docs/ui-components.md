# UI Components

All components live in `src/components/ui/` and export from `src/components/ui/index.ts`.

Import: `import { Button, Card, Badge } from '@/components/ui'`

---

## Design Tokens

Defined in `src/index.css` via Tailwind v4 `@theme`.

| Token | Value | Usage |
|---|---|---|
| `--color-bg` | `#F7F6F3` | Page background |
| `--color-surface` | `#FFFFFF` | Cards, inputs |
| `--color-surface-raised` | `#F2F1EE` | Hover, disabled |
| `--color-border` | `#E3E2DD` | Borders |
| `--color-fg` | `#1A1916` | Primary text |
| `--color-fg-secondary` | `#57564F` | Secondary text |
| `--color-fg-muted` | `#93928B` | Placeholders, hints |
| `--color-primary` | `#2563EB` | Primary actions |
| `--color-danger` | `#DC2626` | Errors, destructive |
| `--color-success` | `#16A34A` | Success |
| `--color-warning` | `#D97706` | Warning |

Fonts: `Manrope` (body, `font-sans`), `Syne` (display, `font-display`).

---

## Button

**Variants:** `primary` (default) · `secondary` · `destructive` · `outline` · `ghost` · `link`  
**Sizes:** `sm` · `md` (default) · `lg` · `icon` · `icon-sm`

```tsx
<Button>Save</Button>
<Button variant="destructive">Delete</Button>
<Button size="icon"><PlusIcon /></Button>
```

---

## Input

Pass `error={true}` for red border + focus ring. Pairs with `FormField`.

```tsx
<Input placeholder="Enter value" />
<Input type="email" error />
```

---

## PasswordInput

`Input` wrapper with show/hide toggle (Eye/EyeOff icons). Same API as `Input`.

```tsx
<PasswordInput placeholder="Password" />
```

---

## Textarea

Same API as `Input`. Resizable vertically by default.

```tsx
<Textarea placeholder="Notes..." rows={4} />
```

---

## Select

Native `<select>` with custom chevron and `Input`-matching styles.

```tsx
<Select>
  <option value="">Choose...</option>
  <option value="active">Active</option>
</Select>
```

---

## Label

Pass `required` to render a red asterisk.

```tsx
<Label htmlFor="email" required>Email</Label>
```

---

## FormField

Composes label + input + hint/error into one block.

```tsx
<FormField label="Email" required htmlFor="email" hint="Used for billing">
  <Input id="email" type="email" />
</FormField>

<FormField label="Plan name" error="Name is required" htmlFor="plan-name">
  <Input id="plan-name" error />
</FormField>
```

---

## Card

**Sub-components:** `Card` · `CardHeader` · `CardTitle` · `CardDescription` · `CardContent` · `CardFooter`

```tsx
<Card>
  <CardHeader>
    <CardTitle>Active Clients</CardTitle>
  </CardHeader>
  <CardContent>42</CardContent>
</Card>
```

---

## Badge

**Variants:** `default` · `primary` · `success` · `warning` · `danger` · `info`

```tsx
<Badge variant="success">Active</Badge>
<Badge variant="danger">Cancelled</Badge>
```

---

## Alert

Each variant renders matching Lucide icon automatically.

**Variants:** `default` · `info` · `success` · `warning` · `danger`

```tsx
<Alert variant="warning" title="Auto-cancel">Scheduled in 3 days.</Alert>
<Alert variant="danger" title="Webhook error">Last 3 events failed.</Alert>
```

---

## Spinner

Color inherits from `currentColor` — override with `text-*`.

**Sizes:** `sm` · `md` (default) · `lg`

```tsx
<Spinner size="sm" className="text-white" />
```

---

## Checkbox

Native checkbox styled with `accent-color` set to primary blue.

```tsx
<Checkbox checked onChange={handler} />
```

---

## Separator

**Orientations:** `horizontal` (default) · `vertical` (requires explicit height)

```tsx
<Separator />
<Separator orientation="vertical" className="h-6" />
```

---

## Table

**Sub-components:** `Table` · `TableHeader` · `TableBody` · `TableRow` · `TableHead` · `TableCell`  
Wraps in overflow container automatically.

```tsx
<Table>
  <TableHeader>
    <TableRow>
      <TableHead>Client</TableHead>
      <TableHead>Status</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    <TableRow>
      <TableCell>Acme Corp</TableCell>
      <TableCell><Badge variant="success">Active</Badge></TableCell>
    </TableRow>
  </TableBody>
</Table>
```
