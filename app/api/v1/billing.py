"""API endpoints for recurring billing triggers and run telemetry."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import require_admin
from app.core.security import AuthenticatedUser
from app.models.billing import BillingRun
from app.schemas.billing import BillingTriggerRequest, BillingRunResponse
from app.services.billing_engine import BillingEngine

router = APIRouter(prefix="/billing", tags=["Billing Engine"])


@router.post("/trigger", response_model=BillingRunResponse, status_code=status.HTTP_201_CREATED)
def trigger_billing_run(
    payload: Optional[BillingTriggerRequest] = None,
    db: Session = Depends(get_db),
    admin: AuthenticatedUser = Depends(require_admin),
) -> BillingRunResponse:
    """Trigger an automated or manual recurring billing execution.

    Requires Admin privileges.
    Evaluates due active subscriptions, performs concurrency-safe invoicing, and logs full audit trail.
    """
    target_date = payload.target_date if payload else None
    trigger_source = payload.trigger_source if payload else "manual_api"

    run = BillingEngine.trigger_billing(
        db=db,
        target_date=target_date,
        trigger_source=trigger_source,
    )
    return run


@router.get("/runs", response_model=List[BillingRunResponse])
def get_billing_runs(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: AuthenticatedUser = Depends(require_admin),
) -> List[BillingRunResponse]:
    """Retrieve billing execution runs and telemetry.

    Requires Admin privileges.
    """
    query = db.query(BillingRun)
    if status_filter:
        query = query.filter(BillingRun.status == status_filter)

    query = query.order_by(BillingRun.started_at.desc())
    offset = (page - 1) * page_size
    runs = query.offset(offset).limit(page_size).all()
    return runs
