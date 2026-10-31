# Subscription Management System – Brightloop

Subscription Management System – Hackathon Project.

## Member 3: Billing & Payments Engine

Member 3's complete module implementation is located on branch `feature/billing-and-payments`.

### Key Features
- **PostgreSQL Database Schema**: 9 billing entities (`invoices`, `invoice_items`, `invoice_tax_details`, `invoice_discount_details`, `discount_rules`, `tax_rules`, `payments`, `billing_runs`, `billing_attempts`) with UUID PKs, NUMERIC money columns, CHECK constraints, and unique indexes.
- **Recurring Billing Engine**: Concurrency-safe billing-day trigger with row locks (`with_for_update(skip_locked=True)`), idempotency guarantees (`uq_subscription_billing_period`), and savepoint isolation.
- **Tax & Discount Engines**: Admin-controlled rules with decimal precision rounding, date validity checks, usage limits, and immutable invoice snapshots.
- **Invoice Lifecycle**: Strict transition state machine (`Draft` → `Confirmed` → `Paid` and `Cancelled`).
- **Payment Management**: Multi-method support (Credit Card, Bank Transfer, UPI, Cash), partial payment reconciliation, overpayment prevention, and idempotency protection.
- **Automated Integration Tests**: 37 comprehensive integration tests backed by PostgreSQL.

For full architectural documentation, schemas, and endpoint specifications, see:
[docs/BILLING_ARCHITECTURE.md](docs/BILLING_ARCHITECTURE.md)
