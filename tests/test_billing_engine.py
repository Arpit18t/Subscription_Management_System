"""Tests for the recurring billing engine, eligibility, idempotency, and audit trails."""

import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.billing import (
    Invoice,
    BillingRun,
    BillingAttempt,
    DiscountRule,
    TaxRule,
)
from app.models.upstream import Subscription, SubscriptionItem, User, Plan, Product
from app.services.billing_engine import BillingEngine


def test_successful_recurring_invoice_generation(
    db: Session, sample_subscription: Subscription, sample_tax_rule: TaxRule
):
    """Test standard recurring billing run: generates invoice, calculates taxes, advances next_billing_date."""
    now = datetime.now(timezone.utc)
    initial_period_end = sample_subscription.current_period_end
    initial_next_billing = sample_subscription.next_billing_date

    run = BillingEngine.trigger_billing(
        db=db,
        target_date=now,
        trigger_source="automated_test",
    )

    assert run.status == "completed"
    assert run.subscriptions_evaluated == 1
    assert run.invoices_generated == 1
    assert run.failures_count == 0

    # Verify invoice was created
    invoice = db.query(Invoice).filter(Invoice.subscription_id == sample_subscription.id).first()
    assert invoice is not None
    # 2 items * 49.99 = 99.98 subtotal
    assert invoice.subtotal_amount == Decimal("99.98")
    # 18% tax on 99.98 = 18.00
    assert invoice.tax_amount == Decimal("18.00")
    assert invoice.total_amount == Decimal("117.98")
    assert invoice.status == "draft"

    # Verify audit attempt log
    attempt = db.query(BillingAttempt).filter(BillingAttempt.billing_run_id == run.id).first()
    assert attempt is not None
    assert attempt.status == "successful"
    assert attempt.invoice_id == invoice.id

    # Verify subscription dates were updated
    db.refresh(sample_subscription)
    assert sample_subscription.current_period_start == initial_period_end
    assert sample_subscription.next_billing_date > initial_next_billing


def test_duplicate_billing_trigger_idempotency(
    db: Session, sample_subscription: Subscription, sample_tax_rule: TaxRule
):
    """Test that repeated triggers for the same period do not generate duplicate invoices."""
    now = datetime.now(timezone.utc)
    orig_start = sample_subscription.current_period_start
    orig_end = sample_subscription.current_period_end

    # First run: creates invoice and advances dates
    run1 = BillingEngine.trigger_billing(db, target_date=now)
    assert run1.invoices_generated == 1

    invoices_count_before = db.query(Invoice).filter(Invoice.subscription_id == sample_subscription.id).count()
    assert invoices_count_before == 1

    # Reset subscription dates to simulate an interrupted/repeated attempt on the same period
    db.refresh(sample_subscription)
    sample_subscription.current_period_start = orig_start
    sample_subscription.current_period_end = orig_end
    sample_subscription.next_billing_date = orig_end
    db.commit()

    # Second trigger on the exact same period
    run2 = BillingEngine.trigger_billing(db, target_date=now)
    # Evaluated, but skipped duplicate creation
    assert run2.invoices_generated == 0

    # Ensure invoice count is still 1
    invoices_count_after = db.query(Invoice).filter(Invoice.subscription_id == sample_subscription.id).count()
    assert invoices_count_after == 1

    # Verify skipped attempt was logged
    skip_attempt = (
        db.query(BillingAttempt)
        .filter(BillingAttempt.billing_run_id == run2.id, BillingAttempt.status == "skipped")
        .first()
    )
    assert skip_attempt is not None
    assert "already exists" in skip_attempt.error_message


def test_database_rollback_and_isolation_after_failure(
    db: Session, sample_subscription: Subscription, customer_user: User, sample_plan: Plan, sample_product: Product
):
    """Test that failure on one subscription is safely rolled back via savepoint and does not break others."""
    now = datetime.now(timezone.utc)

    # Create a second subscription whose customer is inactive (will fail eligibility check)
    inactive_customer = User(
        email="inactive@brightloop.test",
        full_name="Inactive User",
        role="customer",
        is_active=False,  # Inactive!
    )
    db.add(inactive_customer)
    db.commit()
    db.refresh(inactive_customer)

    bad_sub = Subscription(
        id=uuid.uuid4(),
        customer_id=inactive_customer.id,
        plan_id=sample_plan.id,
        status="active",
        current_period_start=now - timedelta(days=30),
        current_period_end=now,
        next_billing_date=now,
        auto_renew=True,
    )
    db.add(bad_sub)
    db.commit()

    # Run billing engine on both subscriptions
    run = BillingEngine.trigger_billing(db, target_date=now)

    assert run.subscriptions_evaluated == 2
    assert run.invoices_generated == 1   # sample_subscription succeeded
    assert run.failures_count == 1       # bad_sub failed cleanly
    assert run.status == "partially_failed"

    # Verify failure attempt recorded with diagnostic reason
    failed_attempt = (
        db.query(BillingAttempt)
        .filter(BillingAttempt.subscription_id == bad_sub.id, BillingAttempt.status == "failed")
        .first()
    )
    assert failed_attempt is not None
    assert "inactive" in failed_attempt.error_message.lower()


def test_billing_api_trigger_and_runs_endpoints(
    client: TestClient, admin_headers: dict, customer_headers: dict, sample_subscription: Subscription
):
    """Test POST /api/v1/billing/trigger and GET /api/v1/billing/runs via HTTP."""
    # Customer forbidden
    res = client.post("/api/v1/billing/trigger", headers=customer_headers)
    assert res.status_code == 403

    # Admin trigger
    res = client.post("/api/v1/billing/trigger", json={"trigger_source": "manual_test"}, headers=admin_headers)
    assert res.status_code == 201
    run_data = res.json()
    assert run_data["status"] in ("completed", "partially_failed")
    assert run_data["subscriptions_evaluated"] >= 1

    # Query runs
    runs_res = client.get("/api/v1/billing/runs", headers=admin_headers)
    assert runs_res.status_code == 200
    assert len(runs_res.json()) >= 1
