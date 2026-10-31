
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_role
from app.database.connection import get_db
from app.models.user import User
from app.models.password_reset_token import PasswordResetToken
from app.core.config import settings
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    UserResponse,
    TokenResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ForgotPasswordResponse,
    StaffCreate,
)
from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    generate_reset_token,
    hash_reset_token,
    send_reset_email,
)


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


# CUSTOMER REGISTRATION
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_customer(
    user_data: UserRegister,
    db: Session = Depends(get_db),
):

    normalized_email = str(user_data.email).strip().lower()

    existing_user = db.scalar(
        select(User).where(User.email == normalized_email)
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This email is already registered.",
        )

    new_user = User(
        full_name=user_data.full_name,
        email=normalized_email,
        password_hash=hash_password(user_data.password),
        role="customer",
        is_active=True,
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This email is already registered.",
        )

    return new_user


# CUSTOMER LOGIN
@router.post(
    "/login",
    response_model=TokenResponse,
)
def login_customer(
    user_data: UserLogin,
    db: Session = Depends(get_db),
):

    normalized_email = str(user_data.email).strip().lower()

    user = db.scalar(
        select(User).where(User.email == normalized_email)
    )

    if user is None or not verify_password(
        user_data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is inactive.",
        )

    token = create_access_token(
        user_id=user.id,
        role=user.role,
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
    )


# GET CURRENT LOGGED-IN USER
@router.get(
    "/me",
    response_model=UserResponse,
)
def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user


# --------------- Forgot Password ---------------

@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
)
def forgot_password(
    body: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    """Request a password reset link.

    Always returns success to avoid email enumeration.
    """
    normalized_email = str(body.email).strip().lower()

    user = db.scalar(
        select(User).where(User.email == normalized_email)
    )

    if user is not None and user.is_active:
        # Invalidate any existing unused tokens for this user
        existing_tokens = db.scalars(
            select(PasswordResetToken).where(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.used_at.is_(None),
            )
        ).all()

        now = datetime.now(timezone.utc)
        for tok in existing_tokens:
            tok.used_at = now

        # Generate new token
        raw_token, token_hash = generate_reset_token()

        reset_record = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=now + timedelta(
                minutes=settings.reset_token_expire_minutes
            ),
        )

        db.add(reset_record)
        db.commit()

        # Send reset email (prints link in dev mode if SMTP not configured)
        try:
            send_reset_email(user.email, raw_token)
        except Exception:
            # Don't fail the request if email sending fails
            pass

    return ForgotPasswordResponse(
        message="If that email is registered, a reset link has been sent."
    )


# --------------- Reset Password ---------------

@router.post(
    "/reset-password",
    response_model=ForgotPasswordResponse,
)
def reset_password(
    body: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    """Reset password using the token from the email link."""
    token_hash = hash_reset_token(body.token)
    now = datetime.now(timezone.utc)

    reset_record = db.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > now,
        )
    )

    if reset_record is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token.",
        )

    # Fetch the user
    user = db.get(User, reset_record.user_id)

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token.",
        )

    # Update password and mark token as used
    user.password_hash = hash_password(body.new_password)
    reset_record.used_at = now

    db.commit()

    return ForgotPasswordResponse(
        message="Password has been reset successfully."
    )


# --------------- Admin: Create Internal Staff ---------------

@router.post(
    "/staff",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_staff(
    staff_data: StaffCreate,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Create a new internal staff account. Admin only."""
    normalized_email = str(staff_data.email).strip().lower()

    existing = db.scalar(
        select(User).where(User.email == normalized_email)
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This email is already registered.",
        )

    new_staff = User(
        full_name=staff_data.full_name,
        email=normalized_email,
        password_hash=hash_password(staff_data.password),
        role="staff",
        is_active=True,
    )

    try:
        db.add(new_staff)
        db.commit()
        db.refresh(new_staff)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This email is already registered.",
        )

    return new_staff
