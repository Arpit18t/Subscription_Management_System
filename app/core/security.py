"""Security, authentication, and authorization helpers."""

from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class AuthenticatedUser(BaseModel):
    """Normalized authenticated user representation."""
    id: UUID
    email: str
    role: str  # 'admin' or 'customer'
    is_active: bool = True

    @property
    def is_admin(self) -> bool:
        return self.role.lower() == "admin"
