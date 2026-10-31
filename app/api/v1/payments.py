"""API endpoints for payment recording, idempotency, and reconciliation history."""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.core.security import AuthenticatedUser
from app.models.billing import Payment, Invoice
from app.schemas.billing import PaymentCreate, PaymentResponse
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def record_payment(
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> PaymentResponse:
    """Record a payment towards an invoice.

    Supports credit card, bank transfer, UPI, and cash.
    Guarantees idempotency via idempotency_key, prevents overpayments, and reconciles invoice status.
    Customers can only pay their own invoices; Admins can record payments for any invoice.
    """
    invoice = db.query(Invoice).filter(Invoice.id == payload.invoice_id).first()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID '{payload.invoice_id}' not found",
        )

    # Authorization guard: customers can only pay their own invoices
    if not current_user.is_admin and invoice.customer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: cannot record payment for another customer's invoice",
        )

    payment = PaymentService.process_payment(
        db=db,
        invoice_id=payload.invoice_id,
        amount=payload.amount,
        payment_method=payload.payment_method,
        transaction_reference=payload.transaction_reference,
        idempotency_key=payload.idempotency_key,
        customer_id=invoice.customer_id,
        note=payload.note,
    )
    return payment


@router.get("", response_model=List[PaymentResponse])
def list_payments(
    invoice_id: Optional[uuid.UUID] = Query(None),
    customer_id: Optional[uuid.UUID] = Query(None),
    payment_method: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> List[PaymentResponse]:
    """Retrieve payments history with role-based filtering."""
    query = db.query(Payment)

    if not current_user.is_admin:
        query = query.filter(Payment.customer_id == current_user.id)
    elif customer_id:
        query = query.filter(Payment.customer_id == customer_id)

    if invoice_id:
        query = query.filter(Payment.invoice_id == invoice_id)
    if payment_method:
        query = query.filter(Payment.payment_method == payment_method)

    query = query.order_by(Payment.payment_date.desc())
    offset = (page - 1) * page_size
    payments = query.offset(offset).limit(page_size).all()
    return payments

