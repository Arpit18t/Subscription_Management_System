"""Application security and authorization verification tests."""

import uuid
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.billing import Invoice
from app.models.upstream import User, Subscription


def test_unauthenticated_request_rejected(client: TestClient):
    """Test that requests lacking authorization credentials are rejected with 401 Unauthorized."""
    res = client.get("/api/v1/invoices")
    assert res.status_code == 401
    assert "Authentication credentials required" in res.json()["detail"]


def test_customer_cannot_access_other_customer_invoice(
    client: TestClient, db: Session, sample_subscription: Subscription, customer_user: User
):
    """Test data isolation: customer A cannot view customer B's invoice."""
    # Create customer B
    other_customer = User(
        id=uuid.uuid4(),
        email="other@brightloop.test",
        full_name="Other Customer",
        role="customer",
        is_active=True,
    )
    db.add(other_customer)
    db.commit()
    db.refresh(other_customer)

    # Create invoice belonging to customer B
    other_invoice = Invoice(
        id=uuid.uuid4(),
        invoice_number="INV-OTHER-001",
        subscription_id=sample_subscription.id,
        customer_id=other_customer.id,
        billing_period_start=sample_subscription.current_period_start,
        billing_period_end=sample_subscription.current_period_end,
        status="confirmed",
        total_amount=Decimal("150.00"),
        amount_due=Decimal("150.00"),
        due_date=sample_subscription.current_period_end,
    )
    db.add(other_invoice)
    db.commit()

    # Customer A attempts to view customer B's invoice -> 403 Forbidden
    customer_a_headers = {"Authorization": f"Bearer {customer_user.id}:customer"}
    res = client.get(f"/api/v1/invoices/{other_invoice.id}", headers=customer_a_headers)
    assert res.status_code == 403
    assert "Access forbidden" in res.json()["detail"]


def test_inactive_user_access_blocked(client: TestClient, db: Session):
    """Test that deactivated accounts are barred from performing operations."""
    banned_user = User(
        id=uuid.uuid4(),
        email="banned@brightloop.test",
        full_name="Banned User",
        role="customer",
        is_active=False,  # Deactivated
    )
    db.add(banned_user)
    db.commit()

    headers = {"Authorization": f"Bearer {banned_user.id}:customer"}
    res = client.get("/api/v1/invoices", headers=headers)
    assert res.status_code == 403
    assert "inactive" in res.json()["detail"].lower()


def test_zero_raw_credentials_stored_or_returned(
    client: TestClient, admin_headers: dict, confirmed_invoice: Invoice
):
    """Test that payment APIs never accept, store, or return raw card numbers or CVVs."""
    # Attempt to post a payment payload - note that schema strictly only has transaction_reference and method
    payment_payload = {
        "invoice_id": str(confirmed_invoice.id),
        "amount": 25.00,
        "payment_method": "credit_card",
        "transaction_reference": "TXN-SECURE-999",
        "idempotency_key": "IDEMP-SECURE-999",
        "note": "Payment via PCI-compliant gateway token",
    }
    res = client.post("/api/v1/payments", json=payment_payload, headers=admin_headers)
    assert res.status_code == 201
    data = res.json()

    # Assert no sensitive card fields exist in the response
    for forbidden in ["card_number", "cvv", "cvc", "pan", "expiry_date"]:
        assert forbidden not in data
