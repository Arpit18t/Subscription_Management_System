"""Tests for Tax Engine, decimal precision, validity dates, and snapshots."""

import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
from sqlalchemy.orm import Session

from app.models.billing import TaxRule
from app.services.tax_engine import TaxEngine


def test_standard_tax_calculation(db: Session, sample_tax_rule: TaxRule):
    """Test standard 18% tax calculation with ROUND_HALF_UP precision."""
    now = datetime.now(timezone.utc)
    taxable_amount = Decimal("100.00")
    total_tax, applied = TaxEngine.calculate_taxes(db, taxable_amount, now)

    # 100.00 * 18% = 18.00
    assert total_tax == Decimal("18.00")
    assert len(applied) == 1
    assert applied[0].name == "Standard GST"
    assert applied[0].tax_rate == Decimal("18.0000")
    assert applied[0].tax_amount == Decimal("18.00")


def test_tax_rounding_precision(db: Session):
    """Test rounding behavior with fractional amounts (e.g., 8.25% on $19.99)."""
    now = datetime.now(timezone.utc)
    tax_rule = TaxRule(
        id=uuid.uuid4(),
        name="State Sales Tax",
        tax_rate=Decimal("8.2500"),
        is_active=True,
    )
    db.add(tax_rule)
    db.commit()

    taxable_amount = Decimal("19.99")
    total_tax, applied = TaxEngine.calculate_taxes(db, taxable_amount, now)

    # 19.99 * 0.0825 = 1.649175 -> 1.65
    assert total_tax == Decimal("1.65")
    assert applied[0].tax_amount == Decimal("1.65")


def test_inactive_and_expired_tax_rules(db: Session):
    """Test that inactive or expired tax rules are not applied."""
    now = datetime.now(timezone.utc)
    inactive_tax = TaxRule(
        id=uuid.uuid4(),
        name="Inactive Tax",
        tax_rate=Decimal("5.0000"),
        is_active=False,
    )
    expired_tax = TaxRule(
        id=uuid.uuid4(),
        name="Expired 2025 Tax",
        tax_rate=Decimal("10.0000"),
        is_active=True,
        valid_from=now - timedelta(days=60),
        valid_until=now - timedelta(days=1),
    )
    future_tax = TaxRule(
        id=uuid.uuid4(),
        name="Future 2027 Tax",
        tax_rate=Decimal("12.0000"),
        is_active=True,
        valid_from=now + timedelta(days=30),
    )
    db.add_all([inactive_tax, expired_tax, future_tax])
    db.commit()

    total_tax, applied = TaxEngine.calculate_taxes(db, Decimal("100.00"), now)
    assert total_tax == Decimal("0.00")
    assert len(applied) == 0


def test_multiple_active_taxes_cumulative(db: Session):
    """Test cumulative calculation of multiple active tax rules (e.g., State + City tax)."""
    now = datetime.now(timezone.utc)
    state_tax = TaxRule(
        id=uuid.uuid4(),
        name="State Tax",
        tax_rate=Decimal("6.0000"),
        is_active=True,
    )
    city_tax = TaxRule(
        id=uuid.uuid4(),
        name="City Tax",
        tax_rate=Decimal("2.5000"),
        is_active=True,
    )
    db.add_all([state_tax, city_tax])
    db.commit()

    taxable = Decimal("100.00")
    total_tax, applied = TaxEngine.calculate_taxes(db, taxable, now)

    # 6.00 + 2.50 = 8.50
    assert total_tax == Decimal("8.50")
    assert len(applied) == 2

