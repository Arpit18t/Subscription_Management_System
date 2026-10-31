
from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_role
from app.database.connection import get_db
from app.models.product import Product
from app.models.product_variant import ProductVariant, ODOO_BRAND_SURCHARGE
from app.models.user import User
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponseFull,
    ProductResponseCustomer,
    VariantCreate,
    VariantResponse,
)


router = APIRouter(
    prefix="/api/products",
    tags=["Products"],
)


# --------------- Helper ---------------

def _product_or_404(db: Session, product_id: int) -> Product:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )
    return product


# --------------- Product CRUD ---------------

@router.post(
    "/",
    response_model=ProductResponseFull,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    data: ProductCreate,
    current_user: User = Depends(require_role("admin", "staff")),
    db: Session = Depends(get_db),
):
    """Create a new product. Admin and Staff only."""
    product = Product(
        name=data.name,
        product_type=data.product_type,
        sales_price=data.sales_price,
        cost_price=data.cost_price,
        notes=data.notes,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


@router.get(
    "/",
    response_model=List[ProductResponseFull] | List[ProductResponseCustomer],
)
def list_products(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all products. Customers see a limited view (no cost_price)."""
    products = db.scalars(
        select(Product).order_by(Product.id)
    ).all()

    if current_user.role == "customer":
        return [
            ProductResponseCustomer.model_validate(p) for p in products
        ]

    return [ProductResponseFull.model_validate(p) for p in products]


@router.get(
    "/{product_id}",
)
def get_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a single product by ID."""
    product = _product_or_404(db, product_id)

    if current_user.role == "customer":
        return ProductResponseCustomer.model_validate(product)

    return ProductResponseFull.model_validate(product)


@router.put(
    "/{product_id}",
    response_model=ProductResponseFull,
)
def update_product(
    product_id: int,
    data: ProductUpdate,
    current_user: User = Depends(require_role("admin", "staff")),
    db: Session = Depends(get_db),
):
    """Update a product. Admin and Staff only."""
    product = _product_or_404(db, product_id)

    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)

    return product


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_product(
    product_id: int,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Delete a product. Admin only."""
    product = _product_or_404(db, product_id)

    db.delete(product)
    db.commit()


# --------------- Product Variants ---------------

@router.post(
    "/{product_id}/variants",
    response_model=VariantResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_variant(
    product_id: int,
    data: VariantCreate,
    current_user: User = Depends(require_role("admin", "staff")),
    db: Session = Depends(get_db),
):
    """Create a variant for a product. Admin and Staff only.

    If variant_name is 'Odoo Brand', the price is automatically
    set to base sales_price + ₹560. Any user-supplied price is
    ignored for Odoo Brand variants.
    """
    product = _product_or_404(db, product_id)

    variant_name = data.variant_name.strip()

    # Enforce the ₹560 surcharge rule for Odoo Brand
    if variant_name.lower() == "odoo brand":
        variant_price = Decimal(str(product.sales_price)) + ODOO_BRAND_SURCHARGE
    else:
        if data.variant_price is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="variant_price is required for non-Odoo-Brand variants.",
            )
        variant_price = data.variant_price

    variant = ProductVariant(
        product_id=product.id,
        variant_name=variant_name,
        variant_price=variant_price,
    )

    db.add(variant)
    db.commit()
    db.refresh(variant)

    return variant


@router.get(
    "/{product_id}/variants",
    response_model=List[VariantResponse],
)
def list_variants(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all variants for a product."""
    _product_or_404(db, product_id)

    variants = db.scalars(
        select(ProductVariant)
        .where(ProductVariant.product_id == product_id)
        .order_by(ProductVariant.id)
    ).all()

    return variants


@router.delete(
    "/{product_id}/variants/{variant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_variant(
    product_id: int,
    variant_id: int,
    current_user: User = Depends(require_role("admin", "staff")),
    db: Session = Depends(get_db),
):
    """Delete a variant. Admin and Staff only."""
    _product_or_404(db, product_id)

    variant = db.scalar(
        select(ProductVariant).where(
            ProductVariant.id == variant_id,
            ProductVariant.product_id == product_id,
        )
    )

    if variant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variant not found.",
        )

    db.delete(variant)
    db.commit()

