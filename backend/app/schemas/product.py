
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# --------------- Product Schemas ---------------

class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    product_type: str = Field(min_length=1, max_length=50)
    sales_price: Decimal = Field(ge=Decimal("0"))
    cost_price: Decimal = Field(ge=Decimal("0"))
    notes: Optional[str] = None

    @field_validator("sales_price", "cost_price")
    @classmethod
    def validate_price(cls, value: Decimal) -> Decimal:
        if value < 0:
            raise ValueError("Price cannot be negative")
        return value.quantize(Decimal("0.01"))


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    product_type: Optional[str] = Field(None, min_length=1, max_length=50)
    sales_price: Optional[Decimal] = Field(None, ge=Decimal("0"))
    cost_price: Optional[Decimal] = Field(None, ge=Decimal("0"))
    notes: Optional[str] = None

    @field_validator("sales_price", "cost_price")
    @classmethod
    def validate_price(cls, value: Optional[Decimal]) -> Optional[Decimal]:
        if value is not None:
            if value < 0:
                raise ValueError("Price cannot be negative")
            return value.quantize(Decimal("0.01"))
        return value


class ProductResponseFull(BaseModel):
    """Full product response for Admin and Staff — includes cost_price."""
    id: int
    name: str
    product_type: str
    sales_price: Decimal
    cost_price: Decimal
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductResponseCustomer(BaseModel):
    """Customer-facing product response — cost_price is hidden."""
    id: int
    name: str
    product_type: str
    sales_price: Decimal
    notes: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --------------- Product Variant Schemas ---------------

class VariantCreate(BaseModel):
    variant_name: str = Field(min_length=1, max_length=100)

    # Note: variant_price is computed server-side for Odoo Brand.
    # For other variants, the price can be provided.
    variant_price: Optional[Decimal] = Field(None, ge=Decimal("0"))


class VariantResponse(BaseModel):
    id: int
    product_id: int
    variant_name: str
    variant_price: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

