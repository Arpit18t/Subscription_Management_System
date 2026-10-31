"""FastAPI application entrypoint for Brightloop Subscription Management System."""

import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import (
    NotFoundException,
    BusinessRuleViolation,
    ConcurrencyConflictException,
    UnauthorizedException,
    ForbiddenException,
)
from app.api.v1 import api_v1_router

# Configure safe structured logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("brightloop.billing")

app = FastAPI(
    title=settings.APP_NAME,
    description="Member 3: High-reliability Billing & Payments Engine for Brightloop.",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Custom exception handlers for standardized, safe API error responses
@app.exception_handler(NotFoundException)
async def not_found_handler(request: Request, exc: NotFoundException):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": exc.message, "code": exc.code},
    )


@app.exception_handler(BusinessRuleViolation)
async def business_rule_handler(request: Request, exc: BusinessRuleViolation):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.message, "code": exc.code},
    )


@app.exception_handler(ConcurrencyConflictException)
async def concurrency_handler(request: Request, exc: ConcurrencyConflictException):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": exc.message, "code": exc.code},
    )


@app.exception_handler(UnauthorizedException)
async def unauthorized_handler(request: Request, exc: UnauthorizedException):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": exc.message, "code": exc.code},
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(ForbiddenException)
async def forbidden_handler(request: Request, exc: ForbiddenException):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": exc.message, "code": exc.code},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error on {request.url.path}: {str(exc)}", exc_info=settings.DEBUG)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal error occurred while processing your request.", "code": "INTERNAL_SERVER_ERROR"},
    )


@app.get("/health", tags=["Health"])
def health_check():
    """System health check endpoint."""
    return {"status": "healthy", "service": settings.APP_NAME}


# Mount API V1 routes
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

