
from pwdlib import PasswordHash


password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """
    Convert plain password into a secure Argon2 hash.
    """
    return password_hasher.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """
    Verify a login password against its stored hash.
    """
    return password_hasher.verify(
        plain_password,
        hashed_password,
    )
