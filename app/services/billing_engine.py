"""Recurring billing engine with concurrency safety, idempotency, and audit trails."""

import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from app.models.base import utc_now
from app.models.upstream import Subscription, SubscriptionItem, User, Product, Plan
from app.models.billing import (
    Invoice,
    InvoiceItem,
    InvoiceTaxDetail,
    InvoiceDiscountDetail,
    BillingRun,
    BillingAttempt,
)
from app.services.discount_engine import DiscountEngine
from app.services.tax_engine import TaxEngine
from app.core.exceptions import BusinessRuleViolation, ConcurrencyConflictException


class BillingEngine:
    @staticmethod
    def calculate_next_period(
        current_end: datetime, interval: str
    ) -> datetime:
        """Calculate next billing period end based on plan interval."""
        interval_lower = (interval or "monthly").lower()
        if interval_lower == "daily":
            return current_end + timedelta(days=1)
        elif interval_lower == "weekly":
            return current_end + timedelta(days=7)
        elif interval_lower == "yearly":
            return current_end + relativedelta(years=1)
        else:  # default monthly
            return current_end + relativedelta(months=1)

    @staticmethod
    def generate_invoice_number(target_date: datetime) -> str:
        """Generate a cryptographically random, collision-resistant unique invoice number."""
        date_str = target_date.strftime("%Y%m%d")
        unique_suffix = uuid.uuid4().hex[:8].upper()
        return f"INV-{date_str}-{unique_suffix}"

    @classmethod
    def trigger_billing(
        cls,
        db: Session,
        target_date: Optional[datetime] = None,
        trigger_source: str = "manual_api",
        auto_confirm: bool = False,
    ) -> BillingRun:
        """Execute a billing run for all due active subscriptions.

        Guarantees:
        - Row-level lock acquisition to prevent concurrent double-billing.
        - Strict database idempotency check via unique (subscription_id, start, end).
        - Granular savepoint per subscription so one failure does not abort other subscriptions.
        - Comprehensive audit recording of all attempts in billing_attempts.
        """
        run_date = target_date or utc_now()
        if run_date.tzinfo is None:
            run_date = run_date.replace(tzinfo=timezone.utc)

        # 1. Initialize BillingRun record
        billing_run = BillingRun(
            id=uuid.uuid4(),
            trigger_source=trigger_source,
            status="in_progress",
            target_date=run_date,
            subscriptions_evaluated=0,
            invoices_generated=0,
            failures_count=0,
            started_at=utc_now(),
        )
        db.add(billing_run)
        db.commit()
        db.refresh(billing_run)

        # 2. Query due active subscriptions
        # Row-level locking with with_for_update(skip_locked=True) ensures concurrent
        # workers pick different subscriptions without deadlocking or duplicate processing.
        due_subscriptions = (
            db.query(Subscription)
            .filter(
                Subscription.status == "active",
                Subscription.next_billing_date <= run_date,
            )
            .with_for_update(skip_locked=True)
            .all()
        )

        billing_run.subscriptions_evaluated = len(due_subscriptions)

        for sub in due_subscriptions:
            # Use a database SAVEPOINT per subscription for atomic isolation
            savepoint = db.begin_nested()
            try:
                # A. Validate eligibility
                customer = db.query(User).filter(User.id == sub.customer_id).first()
                if not customer or not customer.is_active:
                    raise BusinessRuleViolation(f"Subscription {sub.id} customer is missing or inactive")

                plan = db.query(Plan).filter(Plan.id == sub.plan_id).first()
                plan_interval = plan.billing_interval if plan else "monthly"

                period_start = sub.current_period_start
                period_end = sub.current_period_end

                # B. Idempotency Check: verify no invoice exists for this period
                existing_invoice = (
                    db.query(Invoice)
                    .filter(
                        Invoice.subscription_id == sub.id,
                        Invoice.billing_period_start == period_start,
                        Invoice.billing_period_end == period_end,
                    )
                    .first()
                )
                if existing_invoice:
                    attempt = BillingAttempt(
                        id=uuid.uuid4(),
                        billing_run_id=billing_run.id,
                        subscription_id=sub.id,
                        status="skipped",
                        invoice_id=existing_invoice.id,
                        error_message="Invoice already exists for this billing period (idempotent skip)",
                        attempted_at=utc_now(),
                    )
                    db.add(attempt)
                    savepoint.commit()
                    continue

                # C. Calculate line items pricing
                items = db.query(SubscriptionItem).filter(SubscriptionItem.subscription_id == sub.id).all()
                if not items:
                    # Check if plan itself has a price
                    if plan and plan.price > Decimal("0.00"):
                        # Synthesize a default line item from plan
                        product = db.query(Product).first()
                        if not product:
                            raise BusinessRuleViolation(f"No product available to represent plan {plan.name}")
                        items = [
                            SubscriptionItem(
                                id=uuid.uuid4(),
                                subscription_id=sub.id,
                                product_id=product.id,
                                quantity=1,
                                unit_price=plan.price,
                            )
                        ]
                    else:
                        raise BusinessRuleViolation(f"Subscription {sub.id} has no billable items or plan price")

                subtotal = Decimal("0.00")
                for item in items:
                    item_subtotal = (Decimal(str(item.quantity)) * Decimal(str(item.unit_price))).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                    subtotal += item_subtotal

                # D. Apply discounts
                total_discount, applied_discounts = DiscountEngine.calculate_discounts(
                    db=db,
                    subscription_id=sub.id,
                    items=items,
                    subtotal=subtotal,
                    billing_date=run_date,
                    lock_for_update=True,
                )

                # E. Calculate taxes
                taxable_amount = max(Decimal("0.00"), subtotal - total_discount)
                total_tax, applied_taxes = TaxEngine.calculate_taxes(
                    db=db,
                    taxable_amount=taxable_amount,
                    billing_date=run_date,
                )

                total_amount = (subtotal - total_discount + total_tax).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )

                # F. Create Invoice
                invoice_number = cls.generate_invoice_number(run_date)
                due_date = period_end + timedelta(days=14)

                invoice = Invoice(
                    id=uuid.uuid4(),
                    invoice_number=invoice_number,
                    subscription_id=sub.id,
                    customer_id=customer.id,
                    billing_period_start=period_start,
                    billing_period_end=period_end,
                    status="confirmed" if auto_confirm else "draft",
                    currency="USD",
                    subtotal_amount=subtotal,
                    discount_amount=total_discount,
                    tax_amount=total_tax,
                    total_amount=total_amount,
                    amount_paid=Decimal("0.00"),
                    amount_due=total_amount,
                    due_date=due_date,
                    issued_at=run_date,
                    confirmed_at=run_date if auto_confirm else None,
                    customer_snapshot={
                        "full_name": customer.full_name,
                        "email": customer.email,
                    },
                    created_at=utc_now(),
                    updated_at=utc_now(),
                )
                db.add(invoice)
                db.flush()  # Flush to generate ID and trigger DB constraints

                # G. Create Invoice Items with snapshots
                # Distribute discount and tax proportionally across line items
                discount_ratio = (total_discount / subtotal) if subtotal > 0 else Decimal("0.00")
                tax_ratio = (total_tax / taxable_amount) if taxable_amount > 0 else Decimal("0.00")

                for item in items:
                    product = db.query(Product).filter(Product.id == item.product_id).first()
                    prod_name = product.name if product else "Subscription Product"
                    prod_sku = product.sku if product else None

                    item_sub = (Decimal(str(item.quantity)) * Decimal(str(item.unit_price))).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                    item_disc = (item_sub * discount_ratio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    item_taxable = max(Decimal("0.00"), item_sub - item_disc)
                    item_tax = (item_taxable * tax_ratio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    item_total = (item_sub - item_disc + item_tax).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )

                    inv_item = InvoiceItem(
                        id=uuid.uuid4(),
                        invoice_id=invoice.id,
                        product_id=item.product_id,
                        product_name_snapshot=prod_name,
                        product_sku_snapshot=prod_sku,
                        quantity=item.quantity,
                        unit_price_snapshot=Decimal(str(item.unit_price)),
                        subtotal=item_sub,
                        discount_amount=item_disc,
                        tax_amount=item_tax,
                        total=item_total,
                        created_at=utc_now(),
                    )
                    db.add(inv_item)

                # H. Create Discount Snapshots
                for d in applied_discounts:
                    disc_detail = InvoiceDiscountDetail(
                        id=uuid.uuid4(),
                        invoice_id=invoice.id,
                        discount_rule_id=d.rule_id,
                        discount_code_snapshot=d.code,
                        discount_type_snapshot=d.discount_type,
                        discount_value_snapshot=d.discount_value,
                        applied_discount_amount=d.applied_amount,
                        created_at=utc_now(),
                    )
                    db.add(disc_detail)

                # I. Create Tax Snapshots
                for t in applied_taxes:
                    tax_detail = InvoiceTaxDetail(
                        id=uuid.uuid4(),
                        invoice_id=invoice.id,
                        tax_rule_id=t.rule_id,
                        tax_name_snapshot=t.name,
                        tax_rate_snapshot=t.tax_rate,
                        taxable_amount=t.taxable_amount,
                        tax_amount=t.tax_amount,
                        created_at=utc_now(),
                    )
                    db.add(tax_detail)

                # J. Advance subscription billing period ONLY after successful invoice creation
                next_period_end = cls.calculate_next_period(period_end, plan_interval)
                sub.current_period_start = period_end
                sub.current_period_end = next_period_end
                sub.next_billing_date = next_period_end
                sub.updated_at = utc_now()

                # Record successful attempt
                attempt = BillingAttempt(
                    id=uuid.uuid4(),
                    billing_run_id=billing_run.id,
                    subscription_id=sub.id,
                    status="successful",
                    invoice_id=invoice.id,
                    error_message=None,
                    attempted_at=utc_now(),
                )
                db.add(attempt)

                savepoint.commit()
                billing_run.invoices_generated += 1

            except IntegrityError as ie:
                savepoint.rollback()
                # Unique constraint violation or DB constraint triggered
                billing_run.failures_count += 1
                attempt = BillingAttempt(
                    id=uuid.uuid4(),
                    billing_run_id=billing_run.id,
                    subscription_id=sub.id,
                    status="failed",
                    invoice_id=None,
                    error_message=f"Database constraint violation (idempotency enforced): {str(ie.orig)}",
                    attempted_at=utc_now(),
                )
                db.add(attempt)
                db.commit()

            except Exception as e:
                savepoint.rollback()
                billing_run.failures_count += 1
                attempt = BillingAttempt(
                    id=uuid.uuid4(),
                    billing_run_id=billing_run.id,
                    subscription_id=sub.id,
                    status="failed",
                    invoice_id=None,
                    error_message=str(e),
                    attempted_at=utc_now(),
                )
                db.add(attempt)
                db.commit()

        # Finalize run status
        if billing_run.failures_count == 0:
            billing_run.status = "completed"
        elif billing_run.invoices_generated > 0:
            billing_run.status = "partially_failed"
        else:
            billing_run.status = "failed"

        billing_run.completed_at = utc_now()
        db.commit()
        db.refresh(billing_run)
        return billing_run

