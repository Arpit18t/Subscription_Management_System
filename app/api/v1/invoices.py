"""API endpoints for Invoice query, lifecycle confirmation, and cancellation."""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.api.deps import get_current_user, require_admin
from app.core.security import AuthenticatedUser
from app.models.billing import Invoice
from app.schemas.billing import (
    InvoiceResponse,
    InvoiceDetailResponse,
    InvoiceCancelRequest,
)
from app.services.invoice_service import InvoiceService

router = APIRouter(prefix="/invoices", tags=["Invoices"])


@router.get("", response_model=List[InvoiceResponse])
def list_invoices(
    customer_id: Optional[int] = None,
    subscription_id: Optional[uuid.UUID] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> List[InvoiceResponse]:
    """List invoices with role-based filtering.

    Customers can only view their own invoices. Admins can view all invoices.
    """
    query = db.query(Invoice)

    if not current_user.is_admin:
        # Enforce data isolation for customers
        query = query.filter(Invoice.customer_id == current_user.id)
    elif customer_id:
        query = query.filter(Invoice.customer_id == customer_id)

    if subscription_id:
        query = query.filter(Invoice.subscription_id == subscription_id)
    if status_filter:
        query = query.filter(Invoice.status == status_filter)

    query = query.order_by(Invoice.created_at.desc())
    offset = (page - 1) * page_size
    invoices = query.offset(offset).limit(page_size).all()
    return invoices


@router.get("/{invoice_id}", response_model=InvoiceDetailResponse)
def get_invoice_detail(
    invoice_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> InvoiceDetailResponse:
    """Retrieve complete invoice details including line items, discounts, taxes, and payment history.

    Customers can only view their own invoice details.
    """
    invoice = (
        db.query(Invoice)
        .options(
            joinedload(Invoice.items),
            joinedload(Invoice.tax_details),
            joinedload(Invoice.discount_details),
            joinedload(Invoice.payments),
        )
        .filter(Invoice.id == invoice_id)
        .first()
    )
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID '{invoice_id}' not found",
        )

    if not current_user.is_admin and invoice.customer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: cannot view invoices of another customer",
        )

    return invoice


@router.post("/{invoice_id}/confirm", response_model=InvoiceResponse)
def confirm_invoice(
    invoice_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: AuthenticatedUser = Depends(require_admin),
) -> InvoiceResponse:
    """Transition an invoice from Draft to Confirmed.

    Requires Admin privileges.
    """
    invoice = InvoiceService.confirm_invoice(db, invoice_id)
    return invoice


@router.post("/{invoice_id}/cancel", response_model=InvoiceResponse)
def cancel_invoice(
    invoice_id: uuid.UUID,
    payload: Optional[InvoiceCancelRequest] = None,
    db: Session = Depends(get_db),
    admin: AuthenticatedUser = Depends(require_admin),
) -> InvoiceResponse:
    """Cancel an invoice.

    Requires Admin privileges.
    Allowed only if the invoice has zero payments recorded.
    """
    reason = payload.reason if payload else "Cancelled by admin"
    invoice = InvoiceService.cancel_invoice(db, invoice_id, reason=reason)
    return invoice

