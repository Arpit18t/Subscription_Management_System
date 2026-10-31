"""Tests for invoice lifecycle state transitions and business constraints."""

import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.billing import Invoice
from app.models.upstream import Subscription, User
from app.core.exceptions import BusinessRuleViolation
from app.services.invoice_service import InvoiceService


@pytest.fixture
def sample_invoice(db: Session, sample_subscription: Subscription, customer_user: User) -> Invoice:
    """Create a draft invoice for lifecycle testing."""
    now = datetime.now(timezone.utc)
    inv = Invoice(
        id=uuid.uuid4(),
        invoice_number="INV-TEST-0001",
        subscription_id=sample_subscription.id,
        customer_id=customer_user.id,
        billing_period_start=now - timedelta(days=30),
        billing_period_end=now,
        status="draft",
        currency="USD",
        subtotal_amount=Decimal("100.00"),
        discount_amount=Decimal("0.00"),
        tax_amount=Decimal("18.00"),
        total_amount=Decimal("118.00"),
        amount_paid=Decimal("0.00"),
        amount_due=Decimal("118.00"),
        due_date=now + timedelta(days=14),
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


def test_transition_draft_to_confirmed(db: Session, sample_invoice: Invoice):
    """Test confirming a draft invoice."""
    confirmed = InvoiceService.confirm_invoice(db, sample_invoice.id)
    assert confirmed.status == "confirmed"
    assert confirmed.confirmed_at is not None


def test_transition_draft_to_cancelled(db: Session, sample_invoice: Invoice):
    """Test cancelling a draft invoice."""
    cancelled = InvoiceService.cancel_invoice(db, sample_invoice.id, reason="Customer requested termination")
    assert cancelled.status == "cancelled"
    assert cancelled.cancelled_at is not None
    assert cancelled.cancellation_reason == "Customer requested termination"


def test_transition_confirmed_to_cancelled_without_payments(db: Session, sample_invoice: Invoice):
    """Test cancelling a confirmed invoice that has no payments."""
    confirmed = InvoiceService.confirm_invoice(db, sample_invoice.id)
    cancelled = InvoiceService.cancel_invoice(db, confirmed.id, reason="Admin error correction")
    assert cancelled.status == "cancelled"


def test_cannot_cancel_invoice_with_payments(db: Session, sample_invoice: Invoice):
    """Test that cancelling an invoice with recorded payments is strictly prohibited."""
    confirmed = InvoiceService.confirm_invoice(db, sample_invoice.id)
    confirmed.amount_paid = Decimal("50.00")
    db.commit()

    with pytest.raises(BusinessRuleViolation) as exc:
        InvoiceService.cancel_invoice(db, confirmed.id, reason="Try cancelling with payments")
    assert "Cannot cancel invoice with recorded payments" in str(exc.value)


def test_cannot_cancel_paid_invoice(db: Session, sample_invoice: Invoice):
    """Test that a fully paid invoice cannot be cancelled."""
    confirmed = InvoiceService.confirm_invoice(db, sample_invoice.id)
    confirmed.status = "paid"
    confirmed.amount_paid = confirmed.total_amount
    confirmed.amount_due = Decimal("0.00")
    db.commit()

    with pytest.raises(BusinessRuleViolation) as exc:
        InvoiceService.cancel_invoice(db, confirmed.id)
    assert "Paid invoices cannot be cancelled directly" in str(exc.value)


def test_cannot_confirm_cancelled_invoice(db: Session, sample_invoice: Invoice):
    """Test that a cancelled invoice cannot be confirmed."""
    cancelled = InvoiceService.cancel_invoice(db, sample_invoice.id)

    with pytest.raises(BusinessRuleViolation) as exc:
        InvoiceService.confirm_invoice(db, cancelled.id)
    assert "Cannot confirm invoice in 'cancelled' state" in str(exc.value)


def test_api_confirm_and_cancel_endpoints(
    client: TestClient, admin_headers: dict, customer_headers: dict, sample_invoice: Invoice
):
    """Test HTTP API endpoints for confirm and cancel."""
    # Customer cannot confirm (403 Forbidden)
    res = client.post(f"/api/v1/invoices/{sample_invoice.id}/confirm", headers=customer_headers)
    assert res.status_code == 403

    # Admin confirms successfully (200 OK)
    res = client.post(f"/api/v1/invoices/{sample_invoice.id}/confirm", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "confirmed"

    # Admin cancels successfully (200 OK)
    res = client.post(
        f"/api/v1/invoices/{sample_invoice.id}/cancel",
        json={"reason": "Audit correction"},
        headers=admin_headers,
    )
    assert res.status_code == 200
    assert res.json()["status"] == "cancelled"
