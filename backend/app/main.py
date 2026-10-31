from datetime import date
from decimal import Decimal

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func
from sqlalchemy.orm import Session

from .auth import (
    create_access_token,
    get_current_user,
    require_finance_user,
    verify_password,
)
from .database import Base, engine, get_db
from .models import Invoice, Subscription, User
from .schemas import (
    InvoiceResponse,
    SubscriptionResponse,
    TokenResponse,
    UserResponse,
)

app = FastAPI(
    title="Subscription Management System API",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables when the application starts.
Base.metadata.create_all(bind=engine)


@app.get("/")
def home():
    return {
        "message": "Subscription Management System API is running",
        "docs": "/docs",
    }


@app.post("/auth/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.email == form_data.username)
        .first()
    )

    if (
        user is None
        or not user.is_active
        or not verify_password(form_data.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "access_token": create_access_token(user),
        "token_type": "bearer",
    }


@app.get("/auth/me", response_model=UserResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user


@app.get("/portal/subscriptions", response_model=list[SubscriptionResponse])
def get_my_subscriptions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Subscription)
        .filter(Subscription.customer_id == current_user.id)
        .order_by(Subscription.id.desc())
        .all()
    )


@app.get("/portal/invoices", response_model=list[InvoiceResponse])
def get_my_invoices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Invoice)
        .filter(Invoice.customer_id == current_user.id)
        .order_by(Invoice.due_date.desc())
        .all()
    )


@app.get("/finance/dashboard")
def finance_dashboard(
    finance_user: User = Depends(require_finance_user),
    db: Session = Depends(get_db),
):
    active_subscriptions = (
        db.query(Subscription)
        .filter(Subscription.status == "active")
        .all()
    )

    monthly_revenue = Decimal("0.00")

    for subscription in active_subscriptions:
        amount = Decimal(str(subscription.amount))

        if subscription.billing_cycle.lower() == "monthly":
            monthly_revenue += amount
        elif subscription.billing_cycle.lower() in ("yearly", "annual", "annually"):
            monthly_revenue += amount / Decimal("12")

    invoice_totals = db.query(
        func.coalesce(func.sum(Invoice.amount_paid), 0),
        func.coalesce(func.sum(Invoice.amount - Invoice.amount_paid), 0),
    ).filter(Invoice.status != "cancelled").first()

    collected = Decimal(str(invoice_totals[0]))
    outstanding = Decimal(str(invoice_totals[1]))

    return {
        "active_subscriptions_count": len(active_subscriptions),
        "mrr": round(monthly_revenue, 2),
        "arr": round(monthly_revenue * Decimal("12"), 2),
        "total_revenue_collected": round(collected, 2),
        "total_outstanding": round(max(outstanding, Decimal("0.00")), 2),
    }


@app.get("/finance/overdue-invoices", response_model=list[InvoiceResponse])
def get_overdue_invoices(
    finance_user: User = Depends(require_finance_user),
    db: Session = Depends(get_db),
):
    today = date.today()

    return (
        db.query(Invoice)
        .filter(
            Invoice.due_date < today,
            Invoice.amount > Invoice.amount_paid,
            Invoice.status.notin_(["paid", "cancelled"]),
        )
        .order_by(Invoice.due_date.asc())
        .limit(500)
        .all()
    )