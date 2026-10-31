"""Invoice lifecycle management and state transitions."""

import uuid
from typing import Optional
from sqlalchemy.orm import Session

from app.models.base import utc_now
from app.models.billing import Invoice
from app.core.exceptions import NotFoundException, BusinessRuleViolation


class InvoiceService:
    @staticmethod
    def get_invoice_by_id(db: Session, invoice_id: uuid.UUID) -> Invoice:
        """Fetch an invoice by ID or raise NotFoundException."""
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise NotFoundException(f"Invoice with ID '{invoice_id}' not found")
        return invoice

    @classmethod
    def confirm_invoice(cls, db: Session, invoice_id: uuid.UUID) -> Invoice:
        """Transition invoice lifecycle: Draft -> Confirmed.

        Validation rules:
        - Only 'draft' invoices can be confirmed.
        - Raises BusinessRuleViolation for any invalid transition.
        """
        invoice = cls.get_invoice_by_id(db, invoice_id)

        if invoice.status == "confirmed":
            # Idempotent confirmation
            return invoice

        if invoice.status != "draft":
            raise BusinessRuleViolation(
                f"Cannot confirm invoice in '{invoice.status}' state. Only 'draft' invoices can be confirmed."
            )

        invoice.status = "confirmed"
        invoice.confirmed_at = utc_now()
        invoice.updated_at = utc_now()
        db.commit()
        db.refresh(invoice)
        return invoice

    @classmethod
    def cancel_invoice(
        cls, db: Session, invoice_id: uuid.UUID, reason: Optional[str] = None
    ) -> Invoice:
        """Transition invoice to 'cancelled'.

        Validation rules:
        - Invoices in 'draft' state can be cancelled.
        - Invoices in 'confirmed' state can be cancelled ONLY IF no payments have been made (amount_paid == 0).
        - Invoices in 'paid' state CANNOT be cancelled directly.
        - Already 'cancelled' invoices cannot be cancelled again.
        """
        invoice = cls.get_invoice_by_id(db, invoice_id)

        if invoice.status == "cancelled":
            raise BusinessRuleViolation("Invoice is already cancelled")

        if invoice.status == "paid":
            raise BusinessRuleViolation(
                "Paid invoices cannot be cancelled directly. Issue a credit note or refund instead."
            )

        if invoice.amount_paid > 0:
            raise BusinessRuleViolation(
                f"Cannot cancel invoice with recorded payments (${invoice.amount_paid}). Refund payments first."
            )

        invoice.status = "cancelled"
        invoice.cancelled_at = utc_now()
        invoice.cancellation_reason = reason or "Cancelled by user"
        invoice.updated_at = utc_now()
        db.commit()
        db.refresh(invoice)
        return invoice

