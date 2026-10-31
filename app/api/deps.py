"""FastAPI route dependencies including DB session and Auth/RBAC guards."""

import uuid
from typing import Generator, Optional
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.upstream import User
from app.core.security import AuthenticatedUser

# Default development/test fallback admin ID
DEV_ADMIN_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def get_current_user(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    x_user_role: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> AuthenticatedUser:
    """Extract authenticated user from Authorization header or gateway headers.

    Supports:
    1. 'Bearer admin' -> Admin role
    2. 'Bearer customer' or 'Bearer customer:<uuid>' -> Customer role
    3. 'Bearer <uuid>:<role>' -> Specific user ID and role
    4. X-User-Id and X-User-Role headers
    5. Database User lookup if user exists in DB
    """
    token_str = ""
    if authorization and authorization.lower().startswith("bearer "):
        token_str = authorization[7:].strip()

    user_id = None
    role = "customer"
    email = "user@brightloop.io"

    if x_user_id:
        try:
            user_id = uuid.UUID(x_user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid X-User-Id header format",
            )
        role = (x_user_role or "customer").lower()
    elif token_str:
        if token_str == "admin-token" or token_str == "admin":
            user_id = DEV_ADMIN_ID
            role = "admin"
            email = "admin@brightloop.io"
        elif token_str == "customer-token" or token_str == "customer":
            user_id = uuid.UUID("00000000-0000-0000-0000-000000000002")
            role = "customer"
            email = "customer@brightloop.io"
        elif ":" in token_str:
            parts = token_str.split(":", 1)
            try:
                user_id = uuid.UUID(parts[0])
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid UUID in bearer token",
                )
            role = parts[1].lower()
        else:
            # Try to parse as single UUID
            try:
                user_id = uuid.UUID(token_str)
                # Check DB for user role
                db_user = db.query(User).filter(User.id == user_id).first()
                if db_user:
                    role = db_user.role
                    email = db_user.email
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authorization token",
                )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify if user exists in DB and is active
    if user_id:
        db_user = db.query(User).filter(User.id == user_id).first()
        if db_user:
            if not db_user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account is inactive",
                )
            role = db_user.role
            email = db_user.email

    return AuthenticatedUser(
        id=user_id or uuid.uuid4(),
        email=email,
        role=role,
        is_active=True,
    )


def require_admin(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    """Enforce Admin-only access."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required for this operation",
        )
    return current_user

