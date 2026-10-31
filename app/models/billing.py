"""Billing and Payments entities owned by Member 3.

Entities:
- invoices
- invoice_items
- invoice_tax_details
- invoice_discount_details
- discount_rules
- tax_rules
- payments
- billing_runs
- billing_attempts
"""

import uuid
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    String,
    Boolean,
    Numeric,
    Integer,
    Text,
    DateTime,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    Index,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utc_now


class DiscountRule(Base):
    """Discount rules engine entity."""
    __tablename__ = "discount_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    discount_type: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # 'percentage' or 'fixed_amount'
    discount_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    min_purchase_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    min_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    max_usage_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    current_usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True
    )
    subscription_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    __table_args__ = (
        CheckConstraint(
            "discount_type IN ('percentage', 'fixed_amount')",
            name="ck_discount_type_valid",
        ),
        CheckConstraint("discount_value >= 0", name="ck_discount_value_positive"),
        CheckConstraint(
            "(discount_type != 'percentage') OR (discount_value <= 100)",
            name="ck_discount_percentage_range",
        ),
        CheckConstraint("min_purchase_amount >= 0", name="ck_min_purchase_amount_non_negative"),
        CheckConstraint("min_quantity >= 1", name="ck_min_quantity_positive"),
        CheckConstraint(
            "max_usage_count IS NULL OR current_usage_count <= max_usage_count",
            name="ck_discount_usage_limit",
        ),
        Index("idx_discount_active_dates", "is_active", "start_date", "end_date"),
    )


class TaxRule(Base):
    """Tax calculation rule entity."""
    __tablename__ = "tax_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(6, 4), nullable=False
    )  # Percentage rate e.g. 18.0000 for 18%
    jurisdiction: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    __table_args__ = (
        CheckConstraint("tax_rate >= 0 AND tax_rate <= 100", name="ck_tax_rate_range"),
        Index("idx_tax_rule_active_validity", "is_active", "valid_from", "valid_until"),
    )


class Invoice(Base):
    """Invoice entity representing a billing demand."""
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    invoice_number: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    billing_period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    billing_period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="draft", index=True
    )  # draft, confirmed, paid, cancelled
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    subtotal_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    amount_paid: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    amount_due: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    issued_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    customer_snapshot: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    items: Mapped[List["InvoiceItem"]] = relationship(
        "InvoiceItem", back_populates="invoice", cascade="all, delete-orphan"
    )
    tax_details: Mapped[List["InvoiceTaxDetail"]] = relationship(
        "InvoiceTaxDetail", back_populates="invoice", cascade="all, delete-orphan"
    )
    discount_details: Mapped[List["InvoiceDiscountDetail"]] = relationship(
        "InvoiceDiscountDetail", back_populates="invoice", cascade="all, delete-orphan"
    )
    payments: Mapped[List["Payment"]] = relationship(
        "Payment", back_populates="invoice"
    )

    __table_args__ = (
        UniqueConstraint(
            "subscription_id",
            "billing_period_start",
            "billing_period_end",
            name="uq_subscription_billing_period",
        ),
        CheckConstraint(
            "status IN ('draft', 'confirmed', 'paid', 'cancelled')",
            name="ck_invoice_status_valid",
        ),
        CheckConstraint("subtotal_amount >= 0", name="ck_invoice_subtotal_non_negative"),
        CheckConstraint("discount_amount >= 0", name="ck_invoice_discount_non_negative"),
        CheckConstraint("tax_amount >= 0", name="ck_invoice_tax_non_negative"),
        CheckConstraint("total_amount >= 0", name="ck_invoice_total_non_negative"),
        CheckConstraint("amount_paid >= 0", name="ck_invoice_amount_paid_non_negative"),
        CheckConstraint("amount_due >= 0", name="ck_invoice_amount_due_non_negative"),
        CheckConstraint("amount_paid <= total_amount", name="ck_invoice_no_overpayment"),
        Index("idx_invoice_customer_status", "customer_id", "status"),
    )


class InvoiceItem(Base):
    """Line items on an invoice, capturing pricing snapshots."""
    __tablename__ = "invoice_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    product_name_snapshot: Mapped[str] = mapped_column(String(255), nullable=False)
    product_sku_snapshot: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price_snapshot: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="items")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_invoice_item_quantity_positive"),
        CheckConstraint("unit_price_snapshot >= 0", name="ck_invoice_item_unit_price_non_negative"),
        CheckConstraint("subtotal >= 0", name="ck_invoice_item_subtotal_non_negative"),
        CheckConstraint("discount_amount >= 0", name="ck_invoice_item_discount_non_negative"),
        CheckConstraint("tax_amount >= 0", name="ck_invoice_item_tax_non_negative"),
        CheckConstraint("total >= 0", name="ck_invoice_item_total_non_negative"),
    )


class InvoiceTaxDetail(Base):
    """Historical snapshot of tax rules applied to an invoice."""
    __tablename__ = "invoice_tax_details"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tax_rule_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tax_rules.id", ondelete="SET NULL"), nullable=True
    )
    tax_name_snapshot: Mapped[str] = mapped_column(String(100), nullable=False)
    tax_rate_snapshot: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    taxable_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="tax_details")

    __table_args__ = (
        CheckConstraint("taxable_amount >= 0", name="ck_tax_detail_taxable_non_negative"),
        CheckConstraint("tax_amount >= 0", name="ck_tax_detail_tax_amount_non_negative"),
    )


class InvoiceDiscountDetail(Base):
    """Historical snapshot of discount rules applied to an invoice."""
    __tablename__ = "invoice_discount_details"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    discount_rule_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("discount_rules.id", ondelete="SET NULL"), nullable=True
    )
    discount_code_snapshot: Mapped[str] = mapped_column(String(50), nullable=False)
    discount_type_snapshot: Mapped[str] = mapped_column(String(32), nullable=False)
    discount_value_snapshot: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    applied_discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="discount_details")

    __table_args__ = (
        CheckConstraint(
            "applied_discount_amount >= 0",
            name="ck_discount_detail_applied_amount_non_negative",
        ),
    )


class Payment(Base):
    """Payment transaction record for an invoice."""
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_method: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # 'credit_card', 'bank_transfer', 'upi', 'cash'
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="successful"
    )  # 'pending', 'successful', 'failed', 'refunded'
    payment_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    transaction_reference: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    idempotency_key: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="payments")

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_payment_amount_positive"),
        CheckConstraint(
            "payment_method IN ('credit_card', 'bank_transfer', 'upi', 'cash')",
            name="ck_payment_method_valid",
        ),
        CheckConstraint(
            "status IN ('pending', 'successful', 'failed', 'refunded')",
            name="ck_payment_status_valid",
        ),
        Index("idx_payment_invoice_status", "invoice_id", "status"),
    )


class BillingRun(Base):
    """Execution record of an automated or manual recurring billing trigger."""
    __tablename__ = "billing_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    trigger_source: Mapped[str] = mapped_column(
        String(64), nullable=False, default="manual_api"
    )  # 'manual_api', 'scheduler'
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="in_progress", index=True
    )  # 'in_progress', 'completed', 'failed', 'partially_failed'
    target_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    subscriptions_evaluated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    invoices_generated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failures_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    attempts: Mapped[List["BillingAttempt"]] = relationship(
        "BillingAttempt", back_populates="billing_run", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('in_progress', 'completed', 'failed', 'partially_failed')",
            name="ck_billing_run_status_valid",
        ),
    )


class BillingAttempt(Base):
    """Audit log of individual subscription billing processing attempt."""
    __tablename__ = "billing_attempts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    billing_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("billing_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # 'successful', 'failed', 'skipped'
    invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    billing_run: Mapped["BillingRun"] = relationship("BillingRun", back_populates="attempts")

    __table_args__ = (
        CheckConstraint(
            "status IN ('successful', 'failed', 'skipped')",
            name="ck_billing_attempt_status_valid",
        ),
        Index("idx_billing_attempt_sub_run", "subscription_id", "billing_run_id"),
    )

