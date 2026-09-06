import re

from pydantic import BaseModel, field_validator

from app.security.passwords import is_password_valid

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegisterForm(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not _EMAIL_RE.match(value):
            raise ValueError("Enter a valid email address.")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not is_password_valid(value):
            raise ValueError("Password must be at least 8 characters and include a letter and a number.")
        return value


class LoginForm(BaseModel):
    email: str
    password: str
