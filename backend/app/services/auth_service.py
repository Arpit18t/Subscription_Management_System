
from datetime import datetime, timedelta, timezone
import hashlib
import secrets
import smtplib
from email.mime.text import MIMEText

import jwt
from pwdlib import PasswordHash

from app.core.config import settings


password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Securely hash password using Argon2."""
    return password_hasher.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """Verify entered password against stored hash."""
    return password_hasher.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(user_id: int, role: str) -> str:
    """Generate a signed JWT access token."""

    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(
            minutes=settings.access_token_expire_minutes
        ),
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


# --------------- Password Reset Helpers ---------------

def generate_reset_token() -> tuple[str, str]:
    """Generate a secure random token and its SHA-256 hash.

    Returns (raw_token, token_hash). The raw token is sent
    to the user via email; only the hash is stored in the DB.
    """
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    return raw_token, token_hash


def hash_reset_token(raw_token: str) -> str:
    """Hash a raw reset token for DB lookup."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


def send_reset_email(to_email: str, reset_token: str) -> None:
    """Send a password reset email with a reset link.

    Uses SMTP credentials from environment variables.
    Falls back to printing the link if SMTP is not configured.
    """
    reset_link = (
        f"{settings.frontend_url}/reset-password?token={reset_token}"
    )

    subject = "Brightloop - Password Reset Request"
    body = (
        f"Hello,\n\n"
        f"You requested a password reset for your Brightloop account.\n\n"
        f"Click the link below to reset your password "
        f"(valid for {settings.reset_token_expire_minutes} minutes):\n\n"
        f"{reset_link}\n\n"
        f"If you did not request this, please ignore this email.\n\n"
        f"- Brightloop Team"
    )

    # If SMTP is not configured, log the link (hackathon/dev mode)
    if not settings.smtp_user or not settings.smtp_password:
        print(f"[DEV] Password reset link for {to_email}: {reset_link}")
        return

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from_email or settings.smtp_user
    msg["To"] = to_email

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(msg["From"], [to_email], msg.as_string())
