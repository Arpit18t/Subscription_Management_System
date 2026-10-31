
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User
from app.schemas.auth import UserRegister, UserResponse
from app.services.auth_service import hash_password


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


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

    # Check whether email already exists.
    existing_user = db.scalar(
        select(User).where(
            User.email == normalized_email
        )
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This email is already registered.",
        )

    # Hash password before storing it.
    hashed_password = hash_password(user_data.password)

    new_user = User(
        full_name=user_data.full_name,
        email=normalized_email,
        password_hash=hashed_password,
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
