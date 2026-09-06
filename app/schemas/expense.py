from datetime import date as date_type
from datetime import datetime, timezone
from decimal import ROUND_DOWN, Decimal, InvalidOperation

from pydantic import BaseModel, field_validator


class ExpenseForm(BaseModel):
    amount: Decimal
    category_id: int
    date: date_type
    description: str | None = None

    @field_validator("amount", mode="before")
    @classmethod
    def parse_amount(cls, value: object) -> Decimal:
        if value is None or value == "":
            raise ValueError("Enter an amount.")
        try:
            return Decimal(str(value))
        except InvalidOperation:
            raise ValueError("Enter a valid amount.")

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: Decimal) -> Decimal:
        truncated = value.quantize(Decimal("0.01"), rounding=ROUND_DOWN)
        if truncated <= 0:
            raise ValueError("Amount must be greater than zero.")
        return truncated

    @field_validator("category_id", mode="before")
    @classmethod
    def parse_category_id(cls, value: object) -> int:
        if value is None or value == "":
            raise ValueError("Select a category.")
        try:
            return int(str(value))
        except ValueError:
            raise ValueError("Select a valid category.")

    @field_validator("date", mode="before")
    @classmethod
    def validate_date(cls, value: object) -> date_type:
        if value is None or value == "":
            raise ValueError("Date is required.")
        if isinstance(value, date_type):
            parsed = value
        else:
            try:
                parsed = date_type.fromisoformat(str(value))
            except ValueError:
                raise ValueError("Enter a valid date.")
        if parsed != datetime.now(timezone.utc).date():
            raise ValueError("Date must be today's date.")
        return parsed
