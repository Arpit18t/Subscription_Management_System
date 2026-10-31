"""Tests for payment management, partial payments, reconciliation, and idempotency."""

import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.billing import Invoice, Payment
from app.models.upstream import Subscription, User
from app.services.invoice_service import InvoiceService
from app.services.payment_service import PaymentService
from app.core.exceptions import BusinessRuleViolation, ConcurrencyConflictException




def test_payment_methods_supported(db: Session, confirmed_invoice: Invoice, customer_user: User):
    """Test that credit_card, bank_transfer, upi, and cash are all accepted."""
    methods = ["credit_card", "bank_transfer", "upi", "cash"]
    for idx, method in enumerate(methods):
        pmt = PaymentService.process_payment(
            db=db,
            invoice_id=confirmed_invoice.id,
            amount=Decimal("10.00"),
            payment_method=method,
            transaction_reference=f"TXN-REF-{method}-{idx}",
            idempotency_key=f"IDEMP-{method}-{idx}",
            customer_id=customer_user.id,
        )
        assert pmt.payment_method == method
        assert pmt.status == "successful"


def test_multiple_partial_payments_and_full_reconciliation(
    db: Session, confirmed_invoice: Invoice, customer_user: User
):
    """Test multiple partial payments reconciling to 'paid' when amount_due reaches zero."""
    # Payment 1: $80.00
    pmt1 = PaymentService.process_payment(
        db=db,
        invoice_id=confirmed_invoice.id,
        amount=Decimal("80.00"),
        payment_method="upi",
        transaction_reference="TXN-PART-1",
        idempotency_key="IDEMP-PART-1",
        customer_id=customer_user.id,
    )
    db.refresh(confirmed_invoice)
    assert confirmed_invoice.status == "confirmed"
    assert confirmed_invoice.amount_paid == Decimal("80.00")
    assert confirmed_invoice.amount_due == Decimal("120.00")

    # Payment 2: $120.00 (settles remainder)
    pmt2 = PaymentService.process_payment(
        db=db,
        invoice_id=confirmed_invoice.id,
        amount=Decimal("120.00"),
        payment_method="bank_transfer",
        transaction_reference="TXN-PART-2",
        idempotency_key="IDEMP-PART-2",
        customer_id=customer_user.id,
    )
    db.refresh(confirmed_invoice)
    assert confirmed_invoice.status == "paid"
    assert confirmed_invoice.amount_paid == Decimal("200.00")
    assert confirmed_invoice.amount_due == Decimal("0.00")
    assert confirmed_invoice.paid_at is not None


def test_overpayment_prevention(db: Session, confirmed_invoice: Invoice, customer_user: User):
    """Test that any payment exceeding remaining amount_due is rejected."""
    with pytest.raises(BusinessRuleViolation) as exc:
        PaymentService.process_payment(
            db=db,
            invoice_id=confirmed_invoice.id,
            amount=Decimal("200.01"),  # Exceeds $200.00 by 1 cent
            payment_method="credit_card",
            transaction_reference="TXN-OVERPAY",
            idempotency_key="IDEMP-OVERPAY",
            customer_id=customer_user.id,
        )
    assert "exceeds remaining amount due" in str(exc.value)


def test_cannot_pay_draft_or_cancelled_invoice(db: Session, sample_subscription: Subscription, customer_user: User):
    """Test that payments cannot be applied to draft or cancelled invoices."""
    now = datetime.now(timezone.utc)
    draft_inv = Invoice(
        id=uuid.uuid4(),
        invoice_number="INV-DRAFT-01",
        subscription_id=sample_subscription.id,
        customer_id=customer_user.id,
        billing_period_start=now,
        billing_period_end=now + timedelta(days=30),
        status="draft",
        total_amount=Decimal("100.00"),
        amount_due=Decimal("100.00"),
        due_date=now + timedelta(days=14),
    )
    db.add(draft_inv)
    db.commit()

    with pytest.raises(BusinessRuleViolation) as exc:
        PaymentService.process_payment(
            db=db,
            invoice_id=draft_inv.id,
            amount=Decimal("50.00"),
            payment_method="cash",
            transaction_reference="TXN-DRAFT",
            idempotency_key="IDEMP-DRAFT",
            customer_id=customer_user.id,
        )
    assert "The invoice must be confirmed first" in str(exc.value)


def test_idempotent_duplicate_payment_request(db: Session, confirmed_invoice: Invoice, customer_user: User):
    """Test that identical duplicate payment requests return the original payment safely."""
    key = "IDEMP-RETRY-KEY-999"
    ref = "TXN-ORIG-999"

    pmt1 = PaymentService.process_payment(
        db=db,
        invoice_id=confirmed_invoice.id,
        amount=Decimal("50.00"),
        payment_method="credit_card",
        transaction_reference=ref,
        idempotency_key=key,
        customer_id=customer_user.id,
    )

    # Same request replayed (e.g. network timeout retry)
    pmt2 = PaymentService.process_payment(
        db=db,
        invoice_id=confirmed_invoice.id,
        amount=Decimal("50.00"),
        payment_method="credit_card",
        transaction_reference=ref,
        idempotency_key=key,
        customer_id=customer_user.id,
    )

    assert pmt1.id == pmt2.id
    db.refresh(confirmed_invoice)
    # Total paid should still be $50, not $100!
    assert confirmed_invoice.amount_paid == Decimal("50.00")


def test_conflicting_idempotency_key_rejected(db: Session, confirmed_invoice: Invoice, customer_user: User):
    """Test that reusing an idempotency key with conflicting details is rejected."""
    key = "IDEMP-CONFLICT-KEY"

    PaymentService.process_payment(
        db=db,
        invoice_id=confirmed_invoice.id,
        amount=Decimal("30.00"),
        payment_method="upi",
        transaction_reference="TXN-30",
        idempotency_key=key,
        customer_id=customer_user.id,
    )

    with pytest.raises(ConcurrencyConflictException) as exc:
        PaymentService.process_payment(
            db=db,
            invoice_id=confirmed_invoice.id,
            amount=Decimal("40.00"),  # Different amount!
            payment_method="upi",
            transaction_reference="TXN-40",
            idempotency_key=key,
            customer_id=customer_user.id,
        )
    assert "already been used for another transaction" in str(exc.value)


def test_api_payment_recording_and_isolation(
    client: TestClient, customer_headers: dict, confirmed_invoice: Invoice
):
    """Test POST /api/v1/payments via HTTP API."""
    payload = {
        "invoice_id": str(confirmed_invoice.id),
        "amount": 75.00,
        "payment_method": "credit_card",
        "transaction_reference": "TXN-API-PAY-1",
        "idempotency_key": "IDEMP-API-KEY-1",
        "note": "Online card payment",
    }
    res = client.post("/api/v1/payments", json=payload, headers=customer_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["amount"] == "75.00"
    assert data["status"] == "successful"

    # Query GET /api/v1/payments
    get_res = client.get(f"/api/v1/payments?invoice_id={confirmed_invoice.id}", headers=customer_headers)
    assert get_res.status_code == 200
    assert len(get_res.json()) >= 1
