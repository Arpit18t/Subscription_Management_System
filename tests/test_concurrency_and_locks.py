"""PostgreSQL-backed integration tests for database-specific concurrency, locking, and constraints."""

import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from tests.conftest import TestingSessionLocal
from app.models.billing import Invoice, DiscountRule, Payment
from app.models.upstream import Subscription, SubscriptionItem, User, Plan, Product
from app.services.billing_engine import BillingEngine
from app.services.payment_service import PaymentService
from app.services.discount_engine import DiscountEngine
from app.core.exceptions import BusinessRuleViolation, ConcurrencyConflictException


def test_concurrent_billing_triggers_database_uniqueness(sample_subscription: Subscription):
    """Test that concurrent billing runs on the same subscription cannot generate duplicate invoices.

    Enforced by database-level unique constraint:
    UniqueConstraint('subscription_id', 'billing_period_start', 'billing_period_end', name='uq_subscription_billing_period')
    """
    now = datetime.now(timezone.utc)
    num_threads = 4

    def run_concurrent_trigger():
        session = TestingSessionLocal()
        try:
            return BillingEngine.trigger_billing(session, target_date=now, trigger_source="concurrency_test")
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(run_concurrent_trigger) for _ in range(num_threads)]
        runs = [f.result() for f in as_completed(futures)]

    # Check total invoices created across all threads in the database
    verify_session = TestingSessionLocal()
    try:
        invoices = (
            verify_session.query(Invoice)
            .filter(Invoice.subscription_id == sample_subscription.id)
            .all()
        )
        # Exactly ONE invoice should have been generated for this period!
        assert len(invoices) == 1
    finally:
        verify_session.close()


def test_concurrent_payment_overpayment_prevention():
    """Test that parallel concurrent payment attempts on an invoice prevent overpayment via row-level locking."""
    setup_session = TestingSessionLocal()
    now = datetime.now(timezone.utc)
    try:
        cust = User(
            id=uuid.uuid4(),
            email=f"concur_user_{uuid.uuid4().hex[:6]}@test.com",
            full_name="Concurrent Customer",
            role="customer",
            is_active=True,
        )
        setup_session.add(cust)

        plan = Plan(
            id=uuid.uuid4(),
            name="Test Plan",
            billing_interval="monthly",
            price=Decimal("100.00"),
            is_active=True,
        )
        setup_session.add(plan)
        setup_session.flush()

        sub = Subscription(
            id=uuid.uuid4(),
            customer_id=cust.id,
            plan_id=plan.id,
            status="active",
            current_period_start=now - timedelta(days=30),
            current_period_end=now,
            next_billing_date=now,
            auto_renew=True,
        )
        setup_session.add(sub)
        setup_session.flush()

        # Invoice for $100.00
        inv = Invoice(
            id=uuid.uuid4(),
            invoice_number=f"INV-CONCUR-{uuid.uuid4().hex[:6]}",
            subscription_id=sub.id,
            customer_id=cust.id,
            billing_period_start=now - timedelta(days=30),
            billing_period_end=now,
            status="confirmed",
            subtotal_amount=Decimal("100.00"),
            total_amount=Decimal("100.00"),
            amount_paid=Decimal("0.00"),
            amount_due=Decimal("100.00"),
            due_date=now + timedelta(days=14),
        )
        setup_session.add(inv)
        setup_session.commit()
        invoice_id = inv.id
        customer_id = cust.id
    finally:
        setup_session.close()

    # Launch 5 parallel threads, each attempting to pay $30.00 (Total attempted: $150.00 on a $100.00 invoice)
    num_threads = 5
    successful_payments = []
    rejected_payments = []

    def make_payment(thread_idx: int):
        session = TestingSessionLocal()
        try:
            pmt = PaymentService.process_payment(
                db=session,
                invoice_id=invoice_id,
                amount=Decimal("30.00"),
                payment_method="credit_card",
                transaction_reference=f"TXN-CONCUR-{thread_idx}-{uuid.uuid4().hex[:6]}",
                idempotency_key=f"IDEMP-CONCUR-{thread_idx}-{uuid.uuid4().hex[:6]}",
                customer_id=customer_id,
            )
            return ("success", pmt.amount)
        except BusinessRuleViolation as e:
            return ("rejected", str(e))
        except ConcurrencyConflictException as ce:
            return ("rejected", str(ce))
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(make_payment, i) for i in range(num_threads)]
        for f in as_completed(futures):
            status, res = f.result()
            if status == "success":
                successful_payments.append(res)
            else:
                rejected_payments.append(res)

    # Max 3 payments of $30.00 can succeed ($90.00). 4th ($120.00) or 5th MUST be rejected!
    assert len(successful_payments) <= 3
    assert len(rejected_payments) >= 2

    verify_session = TestingSessionLocal()
    try:
        final_inv = verify_session.query(Invoice).filter(Invoice.id == invoice_id).first()
        # Verify invoice amount_paid never exceeded total_amount!
        assert final_inv.amount_paid <= Decimal("100.00")
        assert final_inv.amount_due >= Decimal("0.00")
    finally:
        verify_session.close()


def test_concurrent_discount_usage_limit():
    """Test that concurrent requests applying a limited-use discount rule do not exceed max_usage_count."""
    setup_session = TestingSessionLocal()
    now = datetime.now(timezone.utc)
    try:
        rule = DiscountRule(
            id=uuid.uuid4(),
            code=f"FLASH-{uuid.uuid4().hex[:6]}".upper(),
            name="Flash Sale Limited 2 Uses",
            discount_type="fixed_amount",
            discount_value=Decimal("10.00"),
            max_usage_count=2,  # Exactly 2 uses allowed
            current_usage_count=0,
            is_active=True,
        )
        setup_session.add(rule)

        cust = User(
            id=uuid.uuid4(),
            email=f"disc_user_{uuid.uuid4().hex[:6]}@test.com",
            full_name="Discount Customer",
            role="customer",
            is_active=True,
        )
        setup_session.add(cust)

        prod = Product(
            id=uuid.uuid4(),
            name="Widget",
            sku=f"WIDGET-{uuid.uuid4().hex[:6]}",
            price=Decimal("50.00"),
            is_active=True,
        )
        setup_session.add(prod)

        plan = Plan(id=uuid.uuid4(), name="P", billing_interval="monthly", price=Decimal("50.00"), is_active=True)
        setup_session.add(plan)
        setup_session.flush()

        sub = Subscription(
            id=uuid.uuid4(),
            customer_id=cust.id,
            plan_id=plan.id,
            status="active",
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            next_billing_date=now + timedelta(days=30),
            auto_renew=True,
        )
        setup_session.add(sub)
        setup_session.flush()

        item = SubscriptionItem(id=uuid.uuid4(), subscription_id=sub.id, product_id=prod.id, quantity=1, unit_price=Decimal("50.00"))
        setup_session.add(item)
        setup_session.commit()
        rule_code = rule.code
        sub_id = sub.id
    finally:
        setup_session.close()

    # 4 concurrent threads trying to apply this 2-use discount
    def try_apply_discount():
        session = TestingSessionLocal()
        try:
            items = session.query(SubscriptionItem).filter(SubscriptionItem.subscription_id == sub_id).all()
            disc, applied = DiscountEngine.calculate_discounts(
                db=session,
                subscription_id=sub_id,
                items=items,
                subtotal=Decimal("50.00"),
                billing_date=now,
                discount_code=rule_code,
                lock_for_update=True,
            )
            session.commit()
            return ("applied", disc)
        except Exception as e:
            session.rollback()
            return ("rejected", str(e))
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(try_apply_discount) for _ in range(4)]
        results = [f.result() for f in as_completed(futures)]

    applied_count = sum(1 for status, _ in results if status == "applied")
    # At most 2 threads could have applied it
    assert applied_count <= 2

    verify_session = TestingSessionLocal()
    try:
        final_rule = verify_session.query(DiscountRule).filter(DiscountRule.code == rule_code).first()
        assert final_rule.current_usage_count <= 2
    finally:
        verify_session.close()
