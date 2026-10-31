
import re
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)


class UserRegister(BaseModel):

    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=9, max_length=128)

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()

        if len(value) < 2:
            raise ValueError("Name must contain at least 2 characters")

        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:

        if len(value) <= 8:
            raise ValueError("Password must contain more than 8 characters")

        if not re.search(r"[A-Z]", value):
            raise ValueError("Password needs an uppercase letter")

        if not re.search(r"[a-z]", value):
            raise ValueError("Password needs a lowercase letter")

        if not re.search(r"[^A-Za-z0-9\s]", value):
            raise ValueError("Password needs a special character")

        return value


class UserLogin(BaseModel):

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):

    id: int
    full_name: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
