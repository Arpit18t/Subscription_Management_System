"""Tax calculation engine and snapshot generator."""

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.billing import TaxRule


class AppliedTax:
    def __init__(
        self,
        rule_id: Optional[UUID],
        name: str,
        tax_rate: Decimal,
        taxable_amount: Decimal,
        tax_amount: Decimal,
    ):
        self.rule_id = rule_id
        self.name = name
        self.tax_rate = tax_rate
        self.taxable_amount = taxable_amount
        self.tax_amount = tax_amount


class TaxEngine:
    @staticmethod
    def calculate_taxes(
        db: Session,
        taxable_amount: Decimal,
        billing_date: datetime,
    ) -> Tuple[Decimal, List[AppliedTax]]:
        """Calculate applicable taxes based on active tax rules for the given billing date.

        Rules:
        - Only active rules within valid_from and valid_until.
        - Taxable amount = subtotal - discounts.
        - Strict 2-decimal place precision with standard ROUND_HALF_UP.
        - Produces immutable tax snapshots.
        """
        if taxable_amount <= Decimal("0.00"):
            return Decimal("0.00"), []

        # Find all active tax rules valid as of the billing_date
        query = db.query(TaxRule).filter(
            TaxRule.is_active == True,
            or_(TaxRule.valid_from == None, TaxRule.valid_from <= billing_date),
            or_(TaxRule.valid_until == None, TaxRule.valid_until >= billing_date),
        )
        tax_rules = query.all()

        total_tax = Decimal("0.00")
        applied_taxes: List[AppliedTax] = []

        for rule in tax_rules:
            rate = Decimal(str(rule.tax_rate))
            if rate <= Decimal("0.00"):
                continue

            # tax_rate is percentage, e.g. 18.0000 -> 18%
            tax_amount = (taxable_amount * (rate / Decimal("100.00"))).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

            total_tax += tax_amount
            applied_taxes.append(
                AppliedTax(
                    rule_id=rule.id,
                    name=rule.name,
                    tax_rate=rate,
                    taxable_amount=taxable_amount,
                    tax_amount=tax_amount,
                )
            )

        return total_tax, applied_taxes
