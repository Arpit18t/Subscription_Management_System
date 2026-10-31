"""Pydantic schemas for Billing & Payments module."""

from datetime import datetime
from decimal import Decimal
from typing import List, Literal, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ============================================================================
# DISCOUNT RULES
# ============================================================================

class DiscountRuleBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=50, description="Unique discount code (alphanumeric/dashes)")
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    discount_type: Literal["percentage", "fixed_amount"]
    discount_value: Decimal = Field(..., gt=Decimal("0.00"), description="Discount value (amount or percentage)")
    min_purchase_amount: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    min_quantity: int = Field(default=1, ge=1)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    max_usage_count: Optional[int] = Field(default=None, ge=1)
    product_id: Optional[UUID] = None
    subscription_id: Optional[UUID] = None
    is_active: bool = True

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: str) -> str:
        return v.strip().upper()

    @model_validator(mode="after")
    def validate_rules(self) -> "DiscountRuleBase":
        if self.discount_type == "percentage" and self.discount_value > Decimal("100.00"):
            raise ValueError("Percentage discount value cannot exceed 100%")
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValueError("Expiration end_date must be strictly after start_date")
        return self


class DiscountRuleCreate(DiscountRuleBase):
    pass


class DiscountRuleResponse(DiscountRuleBase):
    id: UUID
    current_usage_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# TAX RULES
# ============================================================================

class TaxRuleBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    tax_rate: Decimal = Field(..., ge=Decimal("0.0000"), le=Decimal("100.0000"), description="Tax rate in percentage, e.g. 18.0000 for 18%")
    jurisdiction: Optional[str] = Field(default=None, max_length=100)
    is_active: bool = True
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None

    @model_validator(mode="after")
    def validate_tax_dates(self) -> "TaxRuleBase":
        if self.valid_from and self.valid_until and self.valid_from >= self.valid_until:
            raise ValueError("valid_until must be strictly after valid_from")
        return self


class TaxRuleCreate(TaxRuleBase):
    pass


class TaxRuleResponse(TaxRuleBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# INVOICE ITEMS & DETAILS
# ============================================================================

class InvoiceItemResponse(BaseModel):
    id: UUID
    product_id: UUID
    product_name_snapshot: str
    product_sku_snapshot: Optional[str]
    quantity: int
    unit_price_snapshot: Decimal
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvoiceTaxDetailResponse(BaseModel):
    id: UUID
    tax_rule_id: Optional[UUID]
    tax_name_snapshot: str
    tax_rate_snapshot: Decimal
    taxable_amount: Decimal
    tax_amount: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvoiceDiscountDetailResponse(BaseModel):
    id: UUID
    discount_rule_id: Optional[UUID]
    discount_code_snapshot: str
    discount_type_snapshot: str
    discount_value_snapshot: Decimal
    applied_discount_amount: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# PAYMENTS
# ============================================================================

class PaymentCreate(BaseModel):
    invoice_id: UUID
    amount: Decimal = Field(..., gt=Decimal("0.00"), description="Payment amount must be greater than zero")
    payment_method: Literal["credit_card", "bank_transfer", "upi", "cash"]
    transaction_reference: str = Field(..., min_length=1, max_length=255)
    idempotency_key: str = Field(..., min_length=1, max_length=255)
    note: Optional[str] = None


class PaymentResponse(BaseModel):
    id: UUID
    invoice_id: UUID
    customer_id: UUID
    amount: Decimal
    payment_method: str
    status: str
    payment_date: datetime
    transaction_reference: str
    note: Optional[str]
    idempotency_key: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# INVOICES
# ============================================================================

class InvoiceResponse(BaseModel):
    id: UUID
    invoice_number: str
    subscription_id: UUID
    customer_id: UUID
    billing_period_start: datetime
    billing_period_end: datetime
    status: str
    currency: str
    subtotal_amount: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    amount_paid: Decimal
    amount_due: Decimal
    due_date: datetime
    issued_at: Optional[datetime]
    confirmed_at: Optional[datetime]
    paid_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    cancellation_reason: Optional[str]
    customer_snapshot: Optional[dict]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvoiceDetailResponse(InvoiceResponse):
    items: List[InvoiceItemResponse] = []
    tax_details: List[InvoiceTaxDetailResponse] = []
    discount_details: List[InvoiceDiscountDetailResponse] = []
    payments: List[PaymentResponse] = []

    model_config = ConfigDict(from_attributes=True)


class InvoiceCancelRequest(BaseModel):
    reason: Optional[str] = Field(default="Cancelled by user/admin", max_length=500)


# ============================================================================
# BILLING ENGINE RUNS & ATTEMPTS
# ============================================================================

class BillingTriggerRequest(BaseModel):
    target_date: Optional[datetime] = None
    trigger_source: str = "manual_api"


class BillingAttemptResponse(BaseModel):
    id: UUID
    billing_run_id: UUID
    subscription_id: UUID
    attempt_number: int
    status: str
    invoice_id: Optional[UUID]
    error_message: Optional[str]
    attempted_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BillingRunResponse(BaseModel):
    id: UUID
    trigger_source: str
    status: str
    target_date: datetime
    subscriptions_evaluated: int
    invoices_generated: int
    failures_count: int
    started_at: datetime
    completed_at: Optional[datetime]
    error_summary: Optional[str]
    created_at: datetime
    attempts: Optional[List[BillingAttemptResponse]] = None

    model_config = ConfigDict(from_attributes=True)

