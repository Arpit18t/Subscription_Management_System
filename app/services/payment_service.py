"""Payment processing, idempotency protection, and invoice reconciliation service."""

import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.base import utc_now
from app.models.billing import Invoice, Payment
from app.core.exceptions import (
    NotFoundException,
    BusinessRuleViolation,
    ConcurrencyConflictException,
)


class PaymentService:
    @classmethod
    def process_payment(
        cls,
        db: Session,
        invoice_id: uuid.UUID,
        amount: Decimal,
        payment_method: str,
        transaction_reference: str,
        idempotency_key: str,
        customer_id: int,
        note: Optional[str] = None,
    ) -> Payment:
        """Process a payment against an invoice with concurrency locking and reconciliation.

        Guarantees:
        - Row-level lock on the target invoice to prevent race conditions during concurrent payments.
        - Idempotency protection using unique idempotency_key.
        - Overpayment prevention: rejects any payment exceeding remaining amount_due.
        - Accurate partial payment tracking and automatic reconciliation to 'paid' status.
        - Zero storage of raw card numbers or CVVs.
        """
        clean_key = idempotency_key.strip()
        clean_ref = transaction_reference.strip()
        clean_amount = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        if clean_amount <= Decimal("0.00"):
            raise BusinessRuleViolation("Payment amount must be strictly greater than zero")

        allowed_methods = {"credit_card", "bank_transfer", "upi", "cash"}
        if payment_method not in allowed_methods:
            raise BusinessRuleViolation(
                f"Invalid payment method '{payment_method}'. Allowed: {', '.join(allowed_methods)}"
            )

        # 1. Idempotency check: see if this idempotency key was already processed
        existing_payment = (
            db.query(Payment)
            .filter(Payment.idempotency_key == clean_key)
            .first()
        )
        if existing_payment:
            # If the existing payment has the exact same invoice and amount, return it safely (idempotent replay)
            if existing_payment.invoice_id == invoice_id and existing_payment.amount == clean_amount:
                return existing_payment
            raise ConcurrencyConflictException(
                f"Idempotency key '{clean_key}' has already been used for another transaction"
            )

        # 2. Check transaction reference uniqueness
        existing_ref = (
            db.query(Payment)
            .filter(Payment.transaction_reference == clean_ref)
            .first()
        )
        if existing_ref:
            raise ConcurrencyConflictException(
                f"Transaction reference '{clean_ref}' has already been recorded"
            )

        # 3. Lock the target invoice row to prevent concurrent overpayments
        invoice = (
            db.query(Invoice)
            .filter(Invoice.id == invoice_id)
            .with_for_update()
            .first()
        )
        if not invoice:
            raise NotFoundException(f"Invoice with ID '{invoice_id}' not found")

        # 4. Validate invoice state
        if invoice.status == "draft":
            raise BusinessRuleViolation(
                "Cannot record payment on a 'draft' invoice. The invoice must be confirmed first."
            )
        if invoice.status == "cancelled":
            raise BusinessRuleViolation("Cannot record payment on a 'cancelled' invoice.")
        if invoice.status == "paid" or invoice.amount_due <= Decimal("0.00"):
            raise BusinessRuleViolation("Invoice is already fully settled and paid.")

        # 5. Overpayment prevention
        if clean_amount > invoice.amount_due:
            raise BusinessRuleViolation(
                f"Payment amount of ${clean_amount} exceeds remaining amount due of ${invoice.amount_due}"
            )

        # 6. Create payment record
        payment = Payment(
            id=uuid.uuid4(),
            invoice_id=invoice.id,
            customer_id=customer_id or invoice.customer_id,
            amount=clean_amount,
            payment_method=payment_method,
            status="successful",
            payment_date=utc_now(),
            transaction_reference=clean_ref,
            note=note,
            idempotency_key=clean_key,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        db.add(payment)

        # 7. Reconcile invoice amounts
        invoice.amount_paid = (invoice.amount_paid + clean_amount).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        invoice.amount_due = (invoice.total_amount - invoice.amount_paid).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        if invoice.amount_due <= Decimal("0.00"):
            invoice.amount_due = Decimal("0.00")
            invoice.status = "paid"
            invoice.paid_at = utc_now()

        invoice.updated_at = utc_now()

        try:
            db.commit()
            db.refresh(payment)
            db.refresh(invoice)
        except IntegrityError as ie:
            db.rollback()
            raise ConcurrencyConflictException(
                f"Database constraint error during payment processing: {str(ie.orig)}"
            )

        return payment

