# POS (Cashier) Integration Contract — q-shop POS

Verified against the actual cashier source (`Q-Shop/apps/api/src/modules/integration/`).
This is the exact contract our platform sends and the cashier expects. Keep both
sides in sync with this file.

---

## Base URL & auth

- **Base URL** = the `api_url` the seller enters when connecting. It **must include
  the API prefix** — the cashier serves everything under `/api`
  (`app.setGlobalPrefix('api')`), so the correct value is:

  ```
  https://<cashier-host>/api
  ```

  We call `{api_url}/integration/...`. Because connecting first runs
  `GET {api_url}/integration/store`, a **successful connect proves the URL is
  right** — if `/api` were missing that check would 404 and the connect would fail.

- **Auth header** on every request: `x-api-key: <the tenant key>`
  (the cashier also accepts `Authorization: Bearer <key>`). A missing/invalid key
  → **401** → we surface `pos_invalid_key`.

- Identity headers we also send (optional, percent-encoded because HTTP headers are
  latin-1 and store names can be Arabic): `x-store-name`, `x-store-url`.

---

## Endpoints

| Method | Path (after base) | Purpose |
|--------|-------------------|---------|
| GET  | `/integration/store`    | Connection check → `{ store, provider, productCount }` |
| GET  | `/integration/products` | The cashier catalogue (the source of `product_id`) |
| POST | `/integration/orders`   | Push a placed online order into the cashier log |

---

## `GET /integration/products` — the product id source

Each product the cashier returns looks like:

```json
{ "id": "b1f2…", "name": "…", "name_en": "…", "sku": null,
  "barcode": "5449000000996", "price": 12.0, "cost": 8.0,
  "stock": 34, "category": "المشروبات", "image_url": null, "is_active": true }
```

- On import we store `PosImportedProduct.external_id = product.id` (the cashier's id)
  and link it to our store product.
- **This `id` is the ONLY value valid as `items[].product_id` when pushing an
  order.** The cashier filters order items by `where id IN (sentIds)` against its
  own products and **silently drops anything it doesn't recognise** — so sending our
  store product id would create an order with **zero items**.

---

## `POST /integration/orders` — the exact payload we send

```jsonc
{
  "external_id":     "QSH-000123",   // our order number — idempotency key on the cashier
  "customer_name":   "أحمد علي",
  "customer_phone":  "01000000000",  // cashier find-or-creates the customer by phone
  "address":         "..., القاهرة",
  "notes":           "",
  "total_amount":    150.0,          // REQUIRED, number
  "tax_amount":      0.0,            // number
  "discount_amount": 0.0,            // number
  "payment_method":  "ONLINE",
  "source":          "online",       // marks a fresh online order (for alerts)
  "currency":        "EGP",
  "placed_at":       "2026-07-09T18:30:00+00:00",  // ISO 8601
  "items": [
    { "product_id": "b1f2…",         // MUST be the cashier product id (GET /products)
      "quantity":   2,
      "unit_price": 50.0 }
  ]
}
```

Headers: `x-api-key: <key>`, `Content-Type: application/json`.

Field validation on the cashier (`CreateOrderDto` + global `ValidationPipe`
`{ whitelist: true, transform: true }`): only `total_amount` and `items` are
required; unknown fields are **stripped, not rejected**; numeric strings are coerced.
Our payload matches the DTO exactly.

### Responses

| Status | Body | Meaning | Our handling |
|--------|------|---------|--------------|
| 200/201 | `{ "id": "<txId>" }` | Order recorded (source = ONLINE) | Success — stamp `pos_synced_at`, `pos_reference = id` |
| 200 | `{ "id": "<txId>", "duplicate": true }` | Same `external_id` already pushed (idempotent) | Success (already in the cashier) |
| 401 | — | Bad/missing API key | `pos_invalid_key` |
| 404 | — | Wrong URL / API not deployed | `pos_unavailable` |
| 409 | `{ message, out_of_stock: [{ product_id, requested, available }] }` | Cashier stock too low | `pos_out_of_stock` (shown before payment) |

**We only treat a response as "sent" when it carries an `id`.** No `id` → we raise
`pos_unavailable` and do **not** mark the order synced. We never rely on a local
"sent" flag without the cashier's confirmation.

---

## Rules that make it "all correct"

1. **`api_url` must end with `/api`** (or whatever `API_PREFIX` the cashier deploys).
   A successful connect guarantees this.
2. **Products must be imported from the cashier first** (Settings → connect →
   import). Only imported products have an `external_id`, and only those can be
   pushed. An order whose products aren't imported → we refuse with
   `pos_no_cashier_items` (re-import, then re-send) instead of pushing an empty order.
3. **`product_id` is always the cashier id** (`external_id`), never our store product id.
4. **`external_id` (our order number) is the idempotency key.** Re-sending the same
   order returns the same transaction id with `duplicate: true` — safe. Because we
   never push an empty order, a bad order can't "poison" its idempotency key; after
   fixing the import, a re-send creates the order fresh.
5. **Stock:** before checkout we call `GET /integration/products` to pre-check the
   cashier's live stock (`check_cashier_stock`); the cashier's 409 at push time is the
   final safety net against overselling.

---

## Where this lives in our code

- Client (HTTP, headers, error mapping): `backend/apps/pos/client.py`
- Payload build + confirmation checks: `PosSupplierService.push_order` in `backend/apps/pos/services.py`
- Manual re-send endpoint: `OrderManagePushView` → `POST /api/v1/orders/manage/<id>/push-to-cashier/`
- Auto-push on order confirm: `pos.push_order_to_cashier` Celery task (`backend/apps/pos/tasks.py`)
