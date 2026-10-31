# Brightloop Subscription Management System — Billing & Payments Engine

## Overview
This repository contains the backend implementation of the **Billing & Payments Engine** (Member 3) for the Brightloop Subscription Management System. It is built using FastAPI, PostgreSQL, SQLAlchemy 2.x, Alembic, and Pydantic v2.

---

## Architecture & Database Schema

The Billing module strictly owns 9 entities and integrates cleanly with upstream contracts owned by Member 1 (Auth & Products) and Member 2 (Plans & Quotations).

### Billing-Owned Entities
1. **`invoices`**: Billing demands generated per subscription billing period. Contains UUID primary key, currency, subtotal, discount, tax, total, amount paid, and amount due. Enforces unique invoice numbers and a database-level composite unique constraint `uq_subscription_billing_period(subscription_id, billing_period_start, billing_period_end)`.
2. **`invoice_items`**: Immutable pricing snapshots of product line items (`product_name_snapshot`, `product_sku_snapshot`, `unit_price_snapshot`, `quantity`, `subtotal`, `discount_amount`, `tax_amount`, `total`).
3. **`invoice_tax_details`**: Immutable tax snapshots capturing the exact rate (`tax_rate_snapshot`), tax rule name, taxable base, and calculated tax amount at the moment of invoice creation.
4. **`invoice_discount_details`**: Immutable discount snapshots capturing discount code, type, value, and applied amount.
5. **`discount_rules`**: Configurable promotional rules supporting percentage and fixed amount discounts, minimum purchase amounts, minimum item quantities, validity dates, maximum usage counts, and product-specific or subscription-wide scopes.
6. **`tax_rules`**: Tax jurisdiction configuration with percentage rates, validity periods, and active status flags.
7. **`payments`**: Payment transaction ledger supporting Credit Card, Bank Transfer, UPI, and Cash. Enforces unique `transaction_reference` and unique `idempotency_key` constraints.
8. **`billing_runs`**: High-level execution logs of recurring billing cycles (evaluations, invoices generated, failures count, status).
9. **`billing_attempts`**: Granular per-subscription audit trail recording individual attempt status (`successful`, `failed`, `skipped`) and diagnostic error messages.

---

## Key Engines & Guarantees

### 1. Recurring Billing Engine (`BillingEngine`)
- **Eligibility Validation**: Verifies active subscription status, active customer account, and valid billable items.
- **Concurrency & Idempotency Protection**: Uses PostgreSQL row-level locking (`with_for_update(skip_locked=True)`) alongside a composite unique constraint on `(subscription_id, billing_period_start, billing_period_end)`. Concurrent or repeated billing requests cannot generate duplicate invoices.
- **Fault-Isolated Execution**: Wraps each subscription billing attempt in a database savepoint (`begin_nested()`), guaranteeing that a failure on one subscription is cleanly rolled back and recorded without aborting or invalidating other subscriptions.
- **Period Advancement**: Advances `current_period_start`, `current_period_end`, and `next_billing_date` strictly after successful invoice creation.

### 2. Discount Engine (`DiscountEngine`)
- Evaluates percentage and fixed discounts against product and subscription scopes.
- Enforces validity dates, minimum purchase thresholds, and minimum quantity constraints.
- Row-level lock protection on `max_usage_count` prevents concurrent race conditions from exceeding authorized promotional usage limits.
- Subtotal cap: Total applied discounts can never exceed subtotal (never allows negative invoice totals).

### 3. Tax Engine (`TaxEngine`)
- Automatically queries active tax rules valid for the target billing date.
- Applies taxes to the taxable subtotal (`subtotal - discounts`).
- Implements strict financial rounding using Python `Decimal` with `ROUND_HALF_UP` to two decimal places.
- Stores immutable snapshots in `invoice_tax_details` to prevent historical invoices from changing when future tax laws or rates change.

### 4. Invoice Lifecycle (`InvoiceService`)
- Allowed lifecycle transitions:
  - `Draft` → `Confirmed`
  - `Draft` → `Cancelled`
  - `Confirmed` → `Cancelled` (strictly permitted only when `amount_paid == 0`)
  - `Confirmed` → `Paid` (automatically transitioned by PaymentService upon full settlement)
- Sending and printing are actions, not payment states.

### 5. Payment Management (`PaymentService`)
- Supported methods: Credit Card, Bank Transfer, UPI, Cash.
- Multiple partial payments: tracks `amount_paid` and `amount_due`.
- Automatic reconciliation: sets status to `paid` and records `paid_at` when `amount_due == 0`.
- Overpayment prevention: rejects any payment amount exceeding remaining `amount_due`.
- Duplicate payment prevention: unique `idempotency_key` ensures safe network retries.
- Application security: raw credit card numbers and CVVs are strictly prohibited and never stored.

---

## API Endpoints

| Method | Endpoint | Description | Role Required |
|---|---|---|---|
| `POST` | `/api/v1/billing/trigger` | Trigger recurring billing cycle | Admin |
| `GET` | `/api/v1/billing/runs` | List billing execution history & telemetry | Admin |
| `GET` | `/api/v1/invoices` | List invoices (customer-isolated) | Admin / Customer |
| `GET` | `/api/v1/invoices/{id}` | Get detailed invoice with line items & history | Admin / Customer |
| `POST` | `/api/v1/invoices/{id}/confirm` | Confirm a draft invoice | Admin |
| `POST` | `/api/v1/invoices/{id}/cancel` | Cancel an invoice (zero payments required) | Admin |
| `POST` | `/api/v1/discounts` | Create new promotional discount rule | Admin |
| `GET` | `/api/v1/discounts` | List available discount rules | Admin / Customer |
| `POST` | `/api/v1/payments` | Record payment against confirmed invoice | Admin / Customer |
| `GET` | `/api/v1/payments` | List payments (customer-isolated) | Admin / Customer |
| `GET` | `/health` | Service health check | Public |

---

## Integration Contracts (Upstream Dependencies)

Member 3 expects upstream tables to follow these schemas:
- `users`: `id UUID PK`, `email VARCHAR UNIQUE`, `full_name VARCHAR`, `role VARCHAR ('admin', 'customer')`, `is_active BOOLEAN`.
- `products`: `id UUID PK`, `name VARCHAR`, `sku VARCHAR UNIQUE`, `price NUMERIC(12,2)`, `is_active BOOLEAN`.
- `plans`: `id UUID PK`, `name VARCHAR`, `billing_interval VARCHAR ('daily', 'weekly', 'monthly', 'yearly')`, `price NUMERIC(12,2)`.
- `subscriptions`: `id UUID PK`, `customer_id UUID FK(users.id)`, `plan_id UUID FK(plans.id)`, `status VARCHAR ('active', 'paused', 'cancelled')`, `current_period_start TIMESTAMPTZ`, `current_period_end TIMESTAMPTZ`, `next_billing_date TIMESTAMPTZ`, `auto_renew BOOLEAN`.
- `subscription_items`: `id UUID PK`, `subscription_id UUID FK(subscriptions.id)`, `product_id UUID FK(products.id)`, `quantity INT`, `unit_price NUMERIC(12,2)`.

---

## Running the Application & Tests

### Setup Environment
```bash
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

### Apply Database Migrations
```bash
alembic upgrade head
```

### Run Automated Integration Tests
```bash
pytest -v
```
