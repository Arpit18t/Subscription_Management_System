"""API endpoints for discount rule creation and catalog inspection."""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user, require_admin
from app.core.security import AuthenticatedUser
from app.models.billing import DiscountRule
from app.schemas.billing import DiscountRuleCreate, DiscountRuleResponse
from app.core.exceptions import BusinessRuleViolation

router = APIRouter(prefix="/discounts", tags=["Discounts"])


@router.post("", response_model=DiscountRuleResponse, status_code=status.HTTP_201_CREATED)
def create_discount_rule(
    payload: DiscountRuleCreate,
    db: Session = Depends(get_db),
    admin: AuthenticatedUser = Depends(require_admin),
) -> DiscountRuleResponse:
    """Create a new discount rule.

    Strictly restricted to Admin role.
    """
    existing = db.query(DiscountRule).filter(DiscountRule.code == payload.code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Discount rule with code '{payload.code}' already exists",
        )

    rule = DiscountRule(
        id=uuid.uuid4(),
        code=payload.code,
        name=payload.name,
        description=payload.description,
        discount_type=payload.discount_type,
        discount_value=payload.discount_value,
        min_purchase_amount=payload.min_purchase_amount,
        min_quantity=payload.min_quantity,
        start_date=payload.start_date,
        end_date=payload.end_date,
        max_usage_count=payload.max_usage_count,
        current_usage_count=0,
        product_id=payload.product_id,
        subscription_id=payload.subscription_id,
        is_active=payload.is_active,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.get("", response_model=List[DiscountRuleResponse])
def list_discount_rules(
    is_active: Optional[bool] = Query(None),
    product_id: Optional[uuid.UUID] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> List[DiscountRuleResponse]:
    """Retrieve discount rules."""
    query = db.query(DiscountRule)
    if is_active is not None:
        query = query.filter(DiscountRule.is_active == is_active)
    if product_id is not None:
        query = query.filter(DiscountRule.product_id == product_id)

    query = query.order_by(DiscountRule.created_at.desc())
    offset = (page - 1) * page_size
    rules = query.offset(offset).limit(page_size).all()
    return rules

