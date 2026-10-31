"""Discount calculation and usage enforcement engine."""

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.billing import DiscountRule, InvoiceDiscountDetail
from app.models.upstream import SubscriptionItem
from app.core.exceptions import BusinessRuleViolation


class AppliedDiscount:
    def __init__(
        self,
        rule_id: Optional[UUID],
        code: str,
        discount_type: str,
        discount_value: Decimal,
        applied_amount: Decimal,
    ):
        self.rule_id = rule_id
        self.code = code
        self.discount_type = discount_type
        self.discount_value = discount_value
        self.applied_amount = applied_amount


class DiscountEngine:
    @staticmethod
    def calculate_discounts(
        db: Session,
        subscription_id: UUID,
        items: List[SubscriptionItem],
        subtotal: Decimal,
        billing_date: datetime,
        discount_code: Optional[str] = None,
        lock_for_update: bool = False,
    ) -> Tuple[Decimal, List[AppliedDiscount]]:
        """Evaluate applicable discount rules and calculate total discount.

        Rules:
        - Percentage or fixed amount.
        - Minimum purchase amount check.
        - Minimum quantity check.
        - Start and expiration dates check.
        - Maximum usage count check with atomic locking.
        - Product-specific or subscription-wide check.
        - Total discount never exceeds subtotal (never creates negative total).
        """
        if subtotal <= Decimal("0.00"):
            return Decimal("0.00"), []

        query = db.query(DiscountRule).filter(
            DiscountRule.is_active == True,
            or_(DiscountRule.start_date == None, DiscountRule.start_date <= billing_date),
            or_(DiscountRule.end_date == None, DiscountRule.end_date >= billing_date),
        )

        if discount_code:
            query = query.filter(DiscountRule.code == discount_code.strip().upper())
        else:
            # Automatic rules matching subscription or general
            query = query.filter(
                or_(
                    DiscountRule.subscription_id == subscription_id,
                    DiscountRule.subscription_id == None,
                )
            )

        if lock_for_update:
            # Acquire row-level lock on discount rule rows to prevent race condition on max_usage_count
            rules = query.with_for_update().all()
        else:
            rules = query.all()

        total_discount = Decimal("0.00")
        applied_discounts: List[AppliedDiscount] = []
        remaining_subtotal = subtotal

        for rule in rules:
            if remaining_subtotal <= Decimal("0.00"):
                break

            # 1. Check max usage limit
            if rule.max_usage_count is not None and rule.current_usage_count >= rule.max_usage_count:
                if discount_code:
                    raise BusinessRuleViolation(f"Discount code '{rule.code}' has reached its maximum usage limit")
                continue

            # 2. Scope evaluation: Product-specific vs. Subscription-wide
            applicable_base = Decimal("0.00")
            applicable_quantity = 0

            if rule.product_id:
                # Find matching items
                for item in items:
                    if item.product_id == rule.product_id:
                        item_subtotal = (Decimal(str(item.quantity)) * Decimal(str(item.unit_price))).quantize(
                            Decimal("0.01"), rounding=ROUND_HALF_UP
                        )
                        applicable_base += item_subtotal
                        applicable_quantity += item.quantity
            else:
                # Subscription-wide
                applicable_base = remaining_subtotal
                applicable_quantity = sum(item.quantity for item in items)

            if applicable_base <= Decimal("0.00"):
                continue

            # 3. Minimum purchase amount validation
            if applicable_base < Decimal(str(rule.min_purchase_amount)):
                if discount_code:
                    raise BusinessRuleViolation(
                        f"Discount code '{rule.code}' requires a minimum purchase amount of ${rule.min_purchase_amount}"
                    )
                continue

            # 4. Minimum quantity validation
            if applicable_quantity < rule.min_quantity:
                if discount_code:
                    raise BusinessRuleViolation(
                        f"Discount code '{rule.code}' requires a minimum quantity of {rule.min_quantity}"
                    )
                continue

            # 5. Calculate discount amount
            if rule.discount_type == "percentage":
                rate = Decimal(str(rule.discount_value)) / Decimal("100.00")
                discount_amt = (applicable_base * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            elif rule.discount_type == "fixed_amount":
                discount_amt = min(Decimal(str(rule.discount_value)), applicable_base)
            else:
                continue

            # Cap discount at remaining subtotal
            discount_amt = min(discount_amt, remaining_subtotal)

            if discount_amt > Decimal("0.00"):
                # If locking is enabled, increment current usage atomically
                if lock_for_update:
                    rule.current_usage_count += 1

                total_discount += discount_amt
                remaining_subtotal -= discount_amt

                applied_discounts.append(
                    AppliedDiscount(
                        rule_id=rule.id,
                        code=rule.code,
                        discount_type=rule.discount_type,
                        discount_value=Decimal(str(rule.discount_value)),
                        applied_amount=discount_amt,
                    )
                )

        return total_discount, applied_discounts

