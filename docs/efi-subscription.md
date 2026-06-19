# subscription

Intro to Subscription (Recurrence) feature in Efí API.

## Intro
Recurring billing for clients via subscription plans. Client authorize debit once. No manual monthly invoice. No missed-payment risk.

Subscription = set of transactions generated recurring. To create one: generate a charge, set installment count + periodicity. System repeats same charge. These settings = Subscription Plan.

Subscription billed via boleto or card:

- Credit Card: client enter payment data once, charge auto-debit per plan config. Runs until all installments paid or subscription canceled (by you or client). Card limit check uses monthly value, not full total.
- Bank Slip (Boleto): client get charge by email 10 days before due date, repeats per plan installment count, until canceled. If due date land on weekend/holiday, system auto-shift to next business day.

3 steps to create subscription:
1. Create subscription plan — set periodicity + installment count;
2. Create subscription (inscrição) linked to plan, via One Step or Two Steps;
3. Set subscription payment method + client data.

## How it works

Subscription created with status `new` = ready to activate. Once payment method set, status → `active` = generating recurring charges.

Subscription stays active until cycle ends, or 3 exit reasons:

- Payer cancel via cancel link in confirmation email → status `canceled`;
- Seller cancel via cancel link in dashboard, or webservice endpoint `/subscription/cancel` / SDK `cancelSubscription` → status `canceled`;
- All charges already generated → status `expired` (all configured charges issued).

Watch transaction status to track subscription health. If a transaction can't confirm payment, status = `unpaid`. Seller should act: stop service, retry other payment method, or cancel subscription.

2 payment methods: boleto, card. Boleto: client get boleto per plan repeat count, can email it. Card: charge auto-debit per plan repeat count.

Either payer or seller can cancel anytime. Both get notified by email w/ cancel details.

### Recurrence rules
Next charge dates set based on first charge creation day. Behavior rules:
- If first charge falls on last day of month (31 in 31-day months, 30 in 30-day months, 28 in common Feb, 29 in leap Feb), next charges always land on last day of each month.
  - Example: created 01/31 → 02/28 (or 02/29 leap year) → 03/31 → 04/30, etc.
- If first charge not on last day, next charges land on same numeric day.
  - Example: created 01/29 → 02/28 (or 02/29 leap) → 03/29 → 04/29.
- Common year Feb has 28 days → 28 = last day → recurrence locks to last day of month going forward.
- Leap year Feb has 29 days → 28 not last day → recurrence stays on day 28 every month.

## Create subscription plan

Integrator sets 3 fields:
- name — plan name;
- interval (months) — charge periodicity (e.g. 1 = monthly);
- repeats — how many charges to generate.

POST to `/plan`.

Request
```
POST /v1/plan
{
  "name": "Internet Plan - 10 Mb", // min 1 char, max 255 chars.
  "interval": 1, // billing interval in months. Min 1, max 24.
  "repeats": 12 // optional. Times charge repeats. If omitted, runs indefinitely until plan canceled. Min 2, max 120.
}
```

- Example 1: interval=1, repeats=null → 1 charge/month, monthly recurring, based on first due date chosen.
- Example 2: interval=6, repeats=2 → 1 charge every 6 months, 2 charges total over 12 months (month 6 + month 12).

Response
```
{
  "code": 200, // HTTP 200 = success
  "data": {
    "plan_id": numero_plan_id, // created plan ID
    "name": "Internet Plan - 10 Mb", // plan name
    "interval": 12, // charge interval, months
    "repeats": null, // repeat count - here: indefinite
    "created_at": "2016-06-28 15:48:32" // creation timestamp
  }
}
```

## Edit subscription plan name

Edit name of existing plan. Pass plan_id of target plan.

Request
```
PUT /v1/plan/:id
{
  "name": "New name"
}
```

Response
```
{
  "code": 200 // HTTP 200 = success
}
```

## Cancel subscription plan

Cancel plan anytime. Pass plan_id.

Request
```
DELETE /v1/plan/:id
```

## Create subscription linked to plan — One Step

After plan created, link subscriptions to it. Useful for recurring billing — future charges auto-generate per plan config.

Pass plan_id from earlier step.

POST to `/plan/:id/subscription/one-step`.

`trial_days` attribute: free trial period, credit_card payments only.

Request (boleto/pix)
```
POST /v1/plan/:id/subscription/one-step
{
  "items": [
    {
      "name": "My Product",
      "value": 5990,
      "amount": 1
    }
  ],
  "payment": {
    "banking_billet": {
      "customer": {
        "name": "Gorbadoc Oldbuck",
        "cpf": "94271564656",
        "email": "client_email@server.com.br",
        "phone_number": "5144916523",
        "address": {
          "street": "Avenida Juscelino Kubitschek",
          "number": "909",
          "neighborhood": "Bauxita",
          "zipcode": "35400000",
          "city": "Ouro Preto",
          "complement": "",
          "state": "MG"
        }
      },
      "expire_at": "2023-12-30",
      "configurations": {
        "fine": 200,
        "interest": 33
      },
      "message": "Pay via barcode or QR Code"
    }
  }
}
```

Request (card)
```
POST /v1/plan/:id/subscription/one-step
{
  "items": [
    {
      "name": "My Product",
      "value": 5990,
      "amount": 1
    }
  ],
  "payment": {
    "credit_card": {
      "customer": {
        "name": "Gorbadoc Oldbuck",
        "cpf": "94271564656",
        "email": "client_email@server.com.br",
        "birth": "1990-08-29",
        "phone_number": "5144916523"
      },
      "payment_token": "",
      "billing_address": {
        "street": "Avenida Juscelino Kubitschek",
        "number": "909",
        "neighborhood": "Bauxita",
        "zipcode": "35400000",
        "city": "Ouro Preto",
        "complement": "",
        "state": "MG"
      }
    }
  }
}
```

Response (boleto/pix)
```
{
  "code": 200, // HTTP 200 = success
  "data": {
    "subscription_id": 25329, // created subscription ID
    "status": "active", // active - all charges generating
    "barcode": "00000.00000 00000.000000 00000.000000 0 00000000000000",
    "link": "subscription_boleto_link", // responsive boleto link
    "billet_link":"https_boleto_access_link", // boleto link
    "pdf": {
      "charge": "subscription_boleto_pdf_link" // boleto PDF link
    },
    "expire_at": "2018-12-30", // boleto due date, format YYYY-MM-DD
    "plan": {
      "id": 2758, // created plan ID
      "interval": 1, // charge periodicity, months (1 = monthly)
      "repeats": null // repeat count
      //(default: null = runs indefinitely until plan canceled)
    },
    "charge": {
      "id": 511843, // generated transaction ID
      "status": "waiting", // payment method selected, awaiting confirmation
      "parcel": 1,
      "total": 7900
    },
    "first_execution": "31/10/2018", // first execution date
    "total": 7900,
    "payment": "banking_billet" // payment method (banking_billet = boleto)
  }
}
```

Response (card)
```
{
  "code": 200, // HTTP 200 = success
  "data": {
    "subscription_id": 25328, // created subscription ID
    "status": "active", // active - all charges generating
    "plan": {
      "id": 2758, // created plan ID
      "interval": 1, // charge periodicity, months (1 = monthly)
      "repeats": null // repeat count
      //(default: null = runs indefinitely until plan canceled)
    },
    "charge": {
      "id": 511842, // generated transaction ID
      "status": "waiting", // payment method selected, awaiting confirmation
      "parcel": 1,
      "total": 7900
    },
    "first_execution": "31/10/2018", // first execution date
    "total": 7900,
    "payment": "credit_card" // payment method
  }
}
```

## Create subscription linked to plan — Two Steps

First create subscription + link to plan: item/product/service, value, qty. Then set payment method + customer data, passing charge_id + customer info.

### 1. Create subscription linked to plan

With plan created, link subscriptions to it. Future charges auto-generate per plan config.

Pass plan_id from earlier step.

POST to `/plan/:id/subscription`.

Request
```
POST /v1/plan/:id/subscription
{
  "items": [
    {
      "name": "Internet - Monthly Fee",
      "value": 6990,
      "amount": 1
    }
  ]
}
```

Response
```
{
  "code": 200, // HTTP 200 = success
  "data": {
    "subscription_id": numero_subscription_id, // created subscription ID
    "status": "new", // charge generated, awaiting payment method
    "custom_id": null, // optional custom identifier
    "charges": [
      {
        "charge_id": numero_charge_id, // generated transaction ID
        "status": "new", // charge generated, awaiting payment method
        "total": 6990, // total in cents (6990 = $69.90)
        "parcel": 1 // installment count
      }
    ],
    "created_at": "2016-06-29 10:42:59" // creation timestamp
  }
}
```

### 2. Set subscription payment method + customer data

After plan created + subscription linked, set recurring payment method: boleto or credit card.

Credit Card: client pays per plan periodicity (monthly, quarterly, etc), same value auto-charged each cycle. Customer enters card data only on first payment — later charges auto-process, no re-entry needed.

To create Credit Card subscription: get `payment_token` before calling `POST /v1/subscription/:id/pay`. See payment_token section for details.

Bank Slip: generated per plan repeat count, can email it. Either payer or seller can cancel anytime — both notified by email w/ cancel details.

`trial_days` attribute: free trial period, credit_card payments only.

POST to `/subscription/:id/pay` to set subscription payment method.

Request (boleto/pix)
```
POST /v1/subscription/:id/pay
{
  "payment": {
    "banking_billet": {
      "customer": {
        "name": "Gorbadoc Oldbuck",
        "cpf": "94271564656",
        "email": "client_email@server.com.br",
        "phone_number": "5144916523",
        "address": {
          "street": "Avenida Juscelino Kubitschek",
          "number": "909",
          "neighborhood": "Bauxita",
          "zipcode": "35400000",
          "city": "Ouro Preto",
          "complement": "",
          "state": "MG"
        }
      },
      "expire_at": "2023-12-30",
      "configurations": {
        "fine": 200,
        "interest": 33
      },
      "message": "Pay via barcode or QR Code"
    }
  }
}
```

Request (card)
```
{
  "payment": {
    "credit_card": {
      "customer": {
        "name": "Gorbadoc Oldbuck",
        "cpf": "94271564656",
        "email": "client_email@server.com.br",
        "birth": "1990-08-29",
        "phone_number": "5144916523"
      },
      "payment_token": "",
      "billing_address": {
        "street": "Avenida Juscelino Kubitschek",
        "number": "909",
        "neighborhood": "Bauxita",
        "zipcode": "35400000",
        "city": "Ouro Preto",
        "complement": "",
        "state": "MG"
      }
    }
  }
}
```

Response (boleto/pix)
```
{
  "code": 200, // HTTP 200 = success
  "data": {
    "subscription_id": 25329, // created subscription ID
    "status": "active", // active - all charges generating
    "barcode": "00000.00000 00000.000000 00000.000000 0 00000000000000",
    "link": "subscription_boleto_link", // responsive boleto link
    "billet_link":"https_boleto_access_link", // boleto link
    "pdf": {
      "charge": "subscription_boleto_pdf_link" // boleto PDF link
    },
    "expire_at": "2018-12-30", // boleto due date, format YYYY-MM-DD
    "plan": {
      "id": 2758, // created plan ID
      "interval": 1, // charge periodicity, months (1 = monthly)
      "repeats": null // repeat count
      //(default: null = runs indefinitely until plan canceled)
    },
    "charge": {
      "id": 511843, // generated transaction ID
      "status": "waiting", // payment method selected, awaiting confirmation
      "parcel": 1,
      "total": 7900
    },
    "first_execution": "31/10/2018", // first execution date
    "total": 7900,
    "payment": "banking_billet" // payment method (banking_billet = boleto)
  }
}
```

Response (card)
```
{
  "code": 200, // HTTP 200 = success
  "data": {
    "subscription_id": 25328, // created subscription ID
    "status": "active", // active - all charges generating
    "plan": {
      "id": 2758, // created plan ID
      "interval": 1, // charge periodicity, months (1 = monthly)
      "repeats": null // repeat count
      //(default: null = runs indefinitely until plan canceled)
    },
    "charge": {
      "id": 511842, // generated transaction ID
      "status": "waiting", // payment method selected, awaiting confirmation
      "parcel": 1,
      "total": 7900
    },
    "first_execution": "31/10/2018", // first execution date
    "total": 7900,
    "payment": "credit_card" // payment method
  }
}
```

## Retry subscription credit card payment

Subscription card payments declined for operational reasons (no limit, bad data, temp card issue) → retry payment via API.

No need to redo full charge issuance — faster, cleaner flow.

Request
```
POST /v1/charge/:id/retry
{
  "payment": {
    "credit_card": {
      "customer": {
        "name": "Gorbadoc Oldbuck",
        "cpf": "94271564656",
        "email": "client_email@server.com.br",
        "birth": "1990-08-29",
        "phone_number": "5144916523"
      },
      "billing_address": {
        "street": "Avenida Juscelino Kubitschek",
        "number": "909",
        "neighborhood": "Bauxita",
        "zipcode": "35400000",
        "city": "Ouro Preto",
        "complement": "",
        "state": "MG"
      },
      "payment_token": "75bfce47d230b550f7eaac2a932e0878a934cb3",
      "update_card": true
    }
  }
}
```

Response
```
{
  "code": 200, // HTTP 200 = success
  "data": {
    "installments": 1, // installment count
    "installment_value": 8900, // installment value, cents ($89.00)
    "charge_id": numero_charge_id, // generated transaction ID
    "status": "waiting", // payment method selected, awaiting confirmation
    "total": 8900, // total, cents ($89.00)
    "payment": "credit_card" // payment method
  }
}
```

Lets integrator retry a failed subscription charge. Requirements:
- charge must be credit_card type
- charge must have status `unpaid`

If subscription canceled/disabled, and retry succeeds on last pending charge → subscription auto-reactivates.

## Add `notification_url` / `custom_id` to existing subscription

Set/change transaction metadata anytime. Useful for updating notification URL or modifying custom_id already tied to transactions.

PUT to `/v1/charge/:id/metadata`, where `:id` = target charge_id.

Use cases:
1. Integrator changed server IP tied to notification URL;
2. Integrator updated notification URL for new charges (createCharge) but needs old ones (updateChargeMetadata) updated too;
3. SSL installed on client server — even w/ 301/302 redirect rule, new URL still needed on charges using old one;
4. Integrator created charges w/o notification URL;
5. Modify/add info on custom_id tied to previously generated transactions; other scenarios possible.

Request
```
PUT /v1/subscription/:id/metadata
{
  "notification_url": 'http://your_domain.com/notification', // valid URL receiving transaction status notifications. Max 255 chars.
  "custom_id": 'REF0001' // optional. Link Efí transaction to your system's own ID. Max 255 chars.
}
```

## Edit subscription data

Edit active subscriptions in a plan. Pass fields to edit + subscription_id.

PUT to `/v1/subscription/:id` w/ updated data in body.

Editing existing subscription requires credit_card as payment method.

Request
```
PUT /v1/subscription/:id
{ 
  "plan_id": 3,       
  "customer": {
    "email": "gorbadoc.oldbuck@gmail.com",
    "phone_number": "31123456789"
  },
  "items": [{
    "name": "Product 1",
    "value": 1000,
    "amount": 1
  }],
  "shippings": [{
    "name": "shipping",
    "value": 1800
  }],
  "payment_token": "75bfce47d230b550f7eaac2a932e0878a934cb3"
}
```

## Cancel subscription

Cancel active subscriptions in a plan. Pass subscription_id.

PUT to `/v1/subscription/:id/cancel`.

Request
```
PUT /v1/subscription/:id/cancel
```

## Resend plan link by email

Resend payment link tied to plan. Pass charge_id + valid email to send boleto to.

POST to `/v1/charge/:id/subscription/resend`.

Request
```
POST /v1/charge/:id/subscription/resend
{
  "email": "client_email@server.com.br"
}
```
