"""Tests for Discount Engine, rule validation, authorization, and limits."""

import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.billing import DiscountRule
from app.models.upstream import Subscription, SubscriptionItem, Product
from app.services.discount_engine import DiscountEngine


def test_percentage_discount_calculation(db: Session, sample_subscription: Subscription, sample_product: Product):
    """Test standard percentage discount calculation (e.g. 20% off)."""
    now = datetime.now(timezone.utc)
    rule = DiscountRule(
        id=uuid.uuid4(),
        code="SAVE20",
        name="20 Percent Off",
        discount_type="percentage",
        discount_value=Decimal("20.00"),
        min_purchase_amount=Decimal("0.00"),
        min_quantity=1,
        is_active=True,
    )
    db.add(rule)
    db.commit()

    items = db.query(SubscriptionItem).filter(SubscriptionItem.subscription_id == sample_subscription.id).all()
    # 2 items * 49.99 = 99.98
    subtotal = Decimal("99.98")
    discount_amt, applied = DiscountEngine.calculate_discounts(
        db, sample_subscription.id, items, subtotal, now, discount_code="SAVE20"
    )

    # 99.98 * 0.20 = 19.996 -> 20.00
    assert discount_amt == Decimal("20.00")
    assert len(applied) == 1
    assert applied[0].code == "SAVE20"
    assert applied[0].discount_type == "percentage"


def test_fixed_amount_discount_calculation(db: Session, sample_subscription: Subscription):
    """Test fixed amount discount calculation (e.g. $15.00 off)."""
    now = datetime.now(timezone.utc)
    rule = DiscountRule(
        id=uuid.uuid4(),
        code="FLAT15",
        name="Flat $15 Off",
        discount_type="fixed_amount",
        discount_value=Decimal("15.00"),
        is_active=True,
    )
    db.add(rule)
    db.commit()

    items = db.query(SubscriptionItem).filter(SubscriptionItem.subscription_id == sample_subscription.id).all()
    subtotal = Decimal("100.00")
    discount_amt, applied = DiscountEngine.calculate_discounts(
        db, sample_subscription.id, items, subtotal, now, discount_code="FLAT15"
    )

    assert discount_amt == Decimal("15.00")
    assert len(applied) == 1
    assert applied[0].applied_amount == Decimal("15.00")


def test_discount_cannot_create_negative_total(db: Session, sample_subscription: Subscription):
    """Test that discount amount is capped at subtotal so total is never negative."""
    now = datetime.now(timezone.utc)
    rule = DiscountRule(
        id=uuid.uuid4(),
        code="SUPER500",
        name="$500 Massive Discount",
        discount_type="fixed_amount",
        discount_value=Decimal("500.00"),
        is_active=True,
    )
    db.add(rule)
    db.commit()

    items = db.query(SubscriptionItem).filter(SubscriptionItem.subscription_id == sample_subscription.id).all()
    subtotal = Decimal("50.00")  # Less than discount value
    discount_amt, applied = DiscountEngine.calculate_discounts(
        db, sample_subscription.id, items, subtotal, now, discount_code="SUPER500"
    )

    # Discount capped at subtotal
    assert discount_amt == Decimal("50.00")
    assert subtotal - discount_amt == Decimal("0.00")


def test_discount_expiration(db: Session, sample_subscription: Subscription):
    """Test that expired discount rules are not applied."""
    now = datetime.now(timezone.utc)
    expired_rule = DiscountRule(
        id=uuid.uuid4(),
        code="EXPIRED10",
        name="Expired Discount",
        discount_type="percentage",
        discount_value=Decimal("10.00"),
        start_date=now - timedelta(days=30),
        end_date=now - timedelta(days=1),  # Expired yesterday
        is_active=True,
    )
    db.add(expired_rule)
    db.commit()

    items = db.query(SubscriptionItem).filter(SubscriptionItem.subscription_id == sample_subscription.id).all()
    subtotal = Decimal("100.00")
    discount_amt, applied = DiscountEngine.calculate_discounts(
        db, sample_subscription.id, items, subtotal, now
    )

    assert discount_amt == Decimal("0.00")
    assert len(applied) == 0


def test_discount_max_usage_limit(db: Session, sample_subscription: Subscription):
    """Test that discount rules exceeding max_usage_count are not applied."""
    now = datetime.now(timezone.utc)
    limited_rule = DiscountRule(
        id=uuid.uuid4(),
        code="LIMITED1",
        name="One-Time Discount",
        discount_type="fixed_amount",
        discount_value=Decimal("25.00"),
        max_usage_count=1,
        current_usage_count=1,  # Already used once
        is_active=True,
    )
    db.add(limited_rule)
    db.commit()

    items = db.query(SubscriptionItem).filter(SubscriptionItem.subscription_id == sample_subscription.id).all()
    subtotal = Decimal("100.00")
    discount_amt, applied = DiscountEngine.calculate_discounts(
        db, sample_subscription.id, items, subtotal, now
    )

    assert discount_amt == Decimal("0.00")
    assert len(applied) == 0


def test_discount_minimum_purchase_and_quantity_thresholds(
    db: Session, sample_subscription: Subscription
):
    """Test minimum purchase amount and minimum quantity conditions."""
    now = datetime.now(timezone.utc)
    high_threshold_rule = DiscountRule(
        id=uuid.uuid4(),
        code="HIGHMIN",
        name="High Minimum Discount",
        discount_type="percentage",
        discount_value=Decimal("15.00"),
        min_purchase_amount=Decimal("500.00"),  # Requires $500
        min_quantity=10,                        # Requires 10 items
        is_active=True,
    )
    db.add(high_threshold_rule)
    db.commit()

    items = db.query(SubscriptionItem).filter(SubscriptionItem.subscription_id == sample_subscription.id).all()
    # Sample sub has 2 items with total 99.98 -> below both thresholds
    subtotal = Decimal("99.98")
    discount_amt, applied = DiscountEngine.calculate_discounts(
        db, sample_subscription.id, items, subtotal, now
    )

    assert discount_amt == Decimal("0.00")
    assert len(applied) == 0


def test_unauthorized_discount_creation(client: TestClient, customer_headers: dict):
    """Test that customer role cannot create discount rules (403 Forbidden)."""
    payload = {
        "code": "HACK50",
        "name": "Unauthorized Discount",
        "discount_type": "percentage",
        "discount_value": 50.00,
    }
    response = client.post("/api/v1/discounts", json=payload, headers=customer_headers)
    assert response.status_code == 403
    assert "Admin privileges required" in response.json()["detail"]


def test_admin_successful_discount_creation(client: TestClient, admin_headers: dict):
    """Test that admin can successfully create discount rules."""
    payload = {
        "code": "SUMMER30",
        "name": "Summer Special 30% Off",
        "description": "Seasonal promotional discount",
        "discount_type": "percentage",
        "discount_value": 30.00,
        "min_purchase_amount": 50.00,
        "min_quantity": 1,
        "is_active": True,
    }
    response = client.post("/api/v1/discounts", json=payload, headers=admin_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "SUMMER30"
    assert data["discount_value"] == "30.00"
    assert data["current_usage_count"] == 0

