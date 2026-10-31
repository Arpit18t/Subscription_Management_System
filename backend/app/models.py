from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="customer")
    is_active = Column(Boolean, nullable=False, default=True)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)

    customer_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    plan_name = Column(String(100), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)

    billing_cycle = Column(
        String(20),
        nullable=False,
        default="monthly",
    )

    status = Column(
        String(20),
        nullable=False,
        default="active",
        index=True,
    )

    start_date = Column(Date, nullable=False, default=date.today)


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)

    customer_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    subscription_id = Column(
        Integer,
        ForeignKey("subscriptions.id"),
        nullable=True,
    )

    amount = Column(Numeric(12, 2), nullable=False)

    amount_paid = Column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    due_date = Column(Date, nullable=False, index=True)

    status = Column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)