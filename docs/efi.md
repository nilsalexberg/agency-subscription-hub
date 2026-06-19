# Efi (Gerencianet) Cobranças API — Integration Notes

Payment provider: Efi Pay (formerly Gerencianet). API family: "Cobranças" (charges) v1.
Doc covers: auth, charge creation (card + boleto/pix), card tokenization, installments lookup, webhook notifications.
Goal: enough detail to reimplement in any language/stack.

## Base URLs

- Production: `https://cobrancas.api.efipay.com.br/v1`
- Sandbox/homolog: `https://cobrancas-h.api.efipay.com.br/v1`

Pick by env flag. Sandbox needs separate client_id/secret (different app in Efi dashboard).

## Auth flow (OAuth2 client_credentials)

1. Build Basic auth header: `base64(client_id:client_secret)`.
2. `POST {BASE_URL}/authorize`
   - Headers: `Authorization: Basic <b64>`, `Content-Type: application/json`
   - Body: `{"grant_type": "client_credentials"}`
3. Response 200 → `{"access_token": "..."}` (+ usually `expires_in`, `token_type`).
4. Use `Authorization: Bearer <access_token>` on every later call.
5. Non-200 → body has error info, raise/fail.

Token has expiry (typical OAuth). Code here gets fresh token per Efi instance/request — no caching/refresh logic. For new impl: cache token, refresh on expiry or on 401, don't re-auth every call if avoidable.

## Create charge — `POST {BASE_URL}/charge/one-step`

One endpoint handles both card and boleto/pix charges — `payment` object shape decides type.

Common body:

```json
{
  "metadata": {
    "notification_url": "https://yourdomain.com/webhook/",
    "custom_id": "order-id-or-ref"
  },
  "items": [...],
  "shippings": [...],
  "payment": { ... }
}
```

### items[]

```json
{ "name": "Product name", "value": 1990, "amount": 1 }
```
- `value`: integer, cents (R$19.90 → 1990).
- `amount`: quantity, integer.
- Optional split/marketplace (pay multiple recipients per item):
```json
"marketplace": {
  "repasses": [
    { "payee_code": "efi-payee-code", "percentage": 1000 }
  ]
}
```
  - `percentage`: integer, basis = x100 (10.00% → 1000).
  - `payee_code`: sub-account id registered in Efi dashboard.

### shippings[]

```json
{ "name": "Frete", "value": 500 }
```
Same cents convention.

### payment.credit_card (card charge)

```json
"payment": {
  "credit_card": {
    "customer": { ... },
    "installments": 1,
    "payment_token": "token-from-frontend-sdk",
    "billing_address": { ... }
  }
}
```

### payment.banking_billet (boleto, also returns pix in response)

```json
"payment": {
  "banking_billet": {
    "customer": { "...": "...", "address": { ... } },
    "expire_at": "2026-06-21",
    "message": "free text shown on slip"
  }
}
```
- Note: boleto customer needs `address` nested INSIDE customer object (card charge keeps `billing_address` as sibling field instead). Different shape per payment type — easy bug source, watch closely.
- `expire_at`: `YYYY-MM-DD`, due date.

### customer object

```json
{
  "name": "Full Name",
  "cpf": "00000000000",
  "email": "user@mail.com",
  "birth": "1990-01-01",
  "phone_number": "11999999999"
}
```
All required. `cpf`/`phone_number`: digits only, no formatting chars.

### billing_address / address object

```json
{
  "street": "Rua X",
  "number": "123",
  "neighborhood": "Bairro",
  "zipcode": "01310100",
  "city": "São Paulo",
  "state": "SP",
  "complement": "Apto 1"
}
```
- `zipcode`: digits only (strip dashes).
- `state`: 2-letter UF code.

### Response (200)

```json
{ "data": { "charge_id": 123456, "status": "waiting|paid|unpaid|...", ... } }
```
- Card charge: if `status == "unpaid"`, charge was rejected — check `data.refusal.reason` for decline reason (insufficient funds, etc). Treat as failure even though HTTP was 200.
- Boleto charge: success response includes extra nested fields used by your app:
  - `data.barcode` — boleto barcode number
  - `data.pix.qrcode`, `data.pix.qrcode_image` — pix copy-paste + image, since boleto charge also auto-generates a pix alternative
  - `data.pdf.charge` — link to boleto PDF

### Errors (non-200)

Body shape (typical):
```json
{ "error_description": "...", "property": "/payment/credit_card/billing_address/zipcode" }
```
- `property` path tells which field failed validation — parse it to give field-level user feedback (e.g. regex match on `billing_address/(\w+)`).

## Card tokenization — frontend SDK, NOT a server endpoint

Card PAN/CVV must never touch your backend (PCI scope). Efi ships a JS SDK that tokenizes in-browser:

1. Include Efi JS SDK script.
2. Configure: `EfiPay.CreditCard.setEnvironment('sandbox'|'production').setAccount(ACCOUNT_ID)`
   - `ACCOUNT_ID` = public account identifier (not client_secret), safe for frontend.
   - Sandbox also supports `.debugger(true)`.
3. Detect brand (needed before tokenizing): `setCardNumber(number).verifyCardBrand()` → resolves brand string (`visa`, `mastercard`, etc). Use brand to also query installment options (see below).
4. Tokenize:
```js
EfiPay.CreditCard
  .setCreditCardData({ brand, number, cvv, expirationMonth, expirationYear, reuse: false })
  .getPaymentToken()
  .then(({ payment_token, card_mask }) => { ... })
```
5. Send only `payment_token` (+ `card_mask` for display) to your backend. Backend passes `payment_token` straight into `payment.credit_card.payment_token` on the charge call above.
6. Errors from SDK carry `error_description` — show to user.

`reuse: false` = token single-use, one charge attempt only (set true if you need a reusable/stored card token, e.g. recurring).

## Installments lookup — `GET {BASE_URL}/installments`

Query params: `brand` (card brand string from tokenize step), `total` (amount in cents, integer).

Response:
```json
{ "data": [
  { "installment": 1, "currency": "199.00", "has_interest": false, "interest_percentage": 0 },
  { "installment": 2, "currency": "104.50", "has_interest": true, "interest_percentage": 250 }
] }
```
- `interest_percentage`: x100 basis again (250 → 2.50%).
- Call this after brand detected + cart total known, before showing installment selector. Re-call if total changes (shipping added, etc).

## Webhooks — payment status updates

Efi does NOT push full payment data to your `notification_url`. It pushes only a token; you must fetch the real data yourself (prevents spoofed webhook payloads).

1. Efi `POST`s to your `notification_url` (set in `metadata.notification_url` at charge creation) with form field `notification=<token>`.
2. Your endpoint must answer `OPTIONS` (CORS preflight) with 200 + `Allow: POST, OPTIONS`, and respond 200 to the actual POST quickly.
3. Server then calls `GET {BASE_URL}/notification/{token}` (Bearer auth) to fetch what changed:
```json
{ "data": [
  { "identifiers": { "charge_id": 123456 }, "status": { "current": "paid" } }
]}
```
4. Match `charge_id` to your stored charge/order, update local status to `status.current`.
5. One notification token can wrap multiple events — iterate the array.

## Gotchas / things to replicate carefully

- Cents everywhere for money, never decimals, on items/shippings/percentage fields.
- `zipcode`/`cpf`/`phone_number`: strip all non-digit chars before sending.
- Card charge HTTP 200 can still mean payment failed (`status: unpaid`) — must inspect body, not just status code.
- Boleto `customer.address` vs card `billing_address` — different nesting per payment type.
- Webhook gives token only — always do the follow-up GET, never trust embedded data if format ever changes to include it directly.
- Sandbox vs production: separate base URL AND separate credentials/account id.
