
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


# The fixed surcharge for the "Odoo Brand" variant.
ODOO_BRAND_SURCHARGE = Decimal("560.00")


class ProductVariant(Base):
    __tablename__ = "product_variants"

    __table_args__ = (
        CheckConstraint(
            "variant_price >= 0",
            name="ck_variant_price_non_negative",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    variant_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    variant_price: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationship back to product
    product = relationship(
        "Product",
        back_populates="variants",
    )

