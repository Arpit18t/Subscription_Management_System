"""Pytest test configuration and database fixtures backed by PostgreSQL."""

import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings
from app.database import get_db
from app.models import (
    Base,
    User,
    Product,
    Plan,
    Subscription,
    SubscriptionItem,
    TaxRule,
    DiscountRule,
    Invoice,
    Payment,
    BillingRun,
    BillingAttempt,
)
from app.main import app

# Connect to real PostgreSQL test database
test_engine = create_engine(
    settings.TEST_DATABASE_URL,
    pool_pre_ping=True,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Ensure all tables exist in the PostgreSQL test database."""
    Base.metadata.create_all(bind=test_engine)
    yield
    # Teardown if necessary


@pytest.fixture
def db() -> Session:
    """Provide a clean isolated DB session for each test."""
    session = TestingSessionLocal()
    try:
        # Clean billing and test tables before test run
        session.execute(text("TRUNCATE TABLE billing_attempts, billing_runs, payments, invoice_discount_details, invoice_tax_details, invoice_items, invoices, discount_rules, tax_rules, subscription_items, subscriptions, plans, products, users CASCADE;"))
        session.commit()
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client(db: Session) -> TestClient:
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db: Session) -> User:
    """Create and return an admin user."""
    admin = User(
        id=uuid.uuid4(),
        email="admin@brightloop.test",
        full_name="Admin Brightloop",
        role="admin",
        is_active=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


@pytest.fixture
def customer_user(db: Session) -> User:
    """Create and return a customer user."""
    customer = User(
        id=uuid.uuid4(),
        email="customer@brightloop.test",
        full_name="Customer Jane Doe",
        role="customer",
        is_active=True,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@pytest.fixture
def admin_headers(admin_user: User) -> dict:
    """Authorization headers for admin."""
    return {"Authorization": f"Bearer {admin_user.id}:admin"}


@pytest.fixture
def customer_headers(customer_user: User) -> dict:
    """Authorization headers for customer."""
    return {"Authorization": f"Bearer {customer_user.id}:customer"}


@pytest.fixture
def sample_product(db: Session) -> Product:
    """Create and return a sample product."""
    product = Product(
        id=uuid.uuid4(),
        name="Pro Analytics Add-on",
        sku="SKU-PRO-ANALYTICS",
        description="Advanced analytics module",
        price=Decimal("49.99"),
        is_active=True,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@pytest.fixture
def sample_plan(db: Session) -> Plan:
    """Create and return a sample monthly subscription plan."""
    plan = Plan(
        id=uuid.uuid4(),
        name="Growth Plan Monthly",
        billing_interval="monthly",
        price=Decimal("99.00"),
        is_active=True,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@pytest.fixture
def sample_subscription(
    db: Session, customer_user: User, sample_plan: Plan, sample_product: Product
) -> Subscription:
    """Create and return an active subscription with line items."""
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=30)
    end = now

    sub = Subscription(
        id=uuid.uuid4(),
        customer_id=customer_user.id,
        plan_id=sample_plan.id,
        status="active",
        current_period_start=start,
        current_period_end=end,
        next_billing_date=end,
        auto_renew=True,
    )
    db.add(sub)
    db.flush()

    sub_item = SubscriptionItem(
        id=uuid.uuid4(),
        subscription_id=sub.id,
        product_id=sample_product.id,
        quantity=2,
        unit_price=sample_product.price,  # 2 * 49.99 = 99.98
    )
    db.add(sub_item)
    db.commit()
    db.refresh(sub)
    return sub


@pytest.fixture
def sample_tax_rule(db: Session) -> TaxRule:
    """Create and return an active 18% GST tax rule."""
    tax = TaxRule(
        id=uuid.uuid4(),
        name="Standard GST",
        tax_rate=Decimal("18.0000"),
        jurisdiction="US-CA",
        is_active=True,
        valid_from=None,
        valid_until=None,
    )
    db.add(tax)
    db.commit()
    db.refresh(tax)
    return tax


@pytest.fixture
def confirmed_invoice(db: Session, sample_subscription: Subscription, customer_user: User) -> Invoice:
    """Create a confirmed invoice with $200.00 total amount for payment testing."""
    now = datetime.now(timezone.utc)
    inv = Invoice(
        id=uuid.uuid4(),
        invoice_number=f"INV-CONF-{uuid.uuid4().hex[:6]}",
        subscription_id=sample_subscription.id,
        customer_id=customer_user.id,
        billing_period_start=now - timedelta(days=30),
        billing_period_end=now,
        status="confirmed",
        currency="USD",
        subtotal_amount=Decimal("200.00"),
        discount_amount=Decimal("0.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("200.00"),
        amount_paid=Decimal("0.00"),
        amount_due=Decimal("200.00"),
        due_date=now + timedelta(days=14),
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv

