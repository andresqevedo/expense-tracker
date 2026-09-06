from decimal import ROUND_DOWN, Decimal, InvalidOperation

from pydantic import BaseModel, field_validator


class BudgetForm(BaseModel):
    amount: Decimal
    category_id: int

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
