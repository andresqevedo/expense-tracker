import re

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_PASSWORD_MIN_LENGTH = 8
_HAS_LETTER = re.compile(r"[A-Za-z]")
_HAS_DIGIT = re.compile(r"\d")


def is_password_valid(password: str) -> bool:
    """Enforce FR-001a: >=8 chars, at least one letter and one digit."""
    return (
        len(password) >= _PASSWORD_MIN_LENGTH
        and bool(_HAS_LETTER.search(password))
        and bool(_HAS_DIGIT.search(password))
    )


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)
