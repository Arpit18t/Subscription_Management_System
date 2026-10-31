"""API v1 routers."""

from fastapi import APIRouter
from app.api.v1.billing import router as billing_router
from app.api.v1.invoices import router as invoices_router
from app.api.v1.discounts import router as discounts_router
from app.api.v1.payments import router as payments_router

api_v1_router = APIRouter()
api_v1_router.include_router(billing_router)
api_v1_router.include_router(invoices_router)
api_v1_router.include_router(discounts_router)
api_v1_router.include_router(payments_router)

__all__ = ["api_v1_router"]

