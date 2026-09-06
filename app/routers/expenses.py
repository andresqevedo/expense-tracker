from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.category import Category
from app.models.expense import Expense
from app.models.user import User
from app.schemas.expense import ExpenseForm
from app.templating import templates

router = APIRouter()


async def _category_options(db: AsyncSession) -> list[Category]:
    result = await db.execute(select(Category).order_by(Category.name))
    return list(result.scalars().all())


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


async def _render_expense_form(
    request: Request,
    db: AsyncSession,
    errors: dict[str, str],
    amount: str,
    category_id: str,
    description: str | None,
):
    categories = await _category_options(db)
    return templates.TemplateResponse(
        request=request,
        name="expense_form.html",
        context={
            "errors": errors,
            "categories": categories,
            "amount": amount,
            "category_id": category_id,
            "description": description or "",
            "today": _today(),
        },
    )


@router.get("/expenses/new")
async def new_expense_form(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _render_expense_form(request, db, {}, "", "", "")


@router.post("/expenses")
async def create_expense(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    form = await request.form()
    amount_raw = str(form.get("amount", ""))
    category_id_raw = str(form.get("category_id", ""))
    date_raw = str(form.get("date", ""))
    description_raw = form.get("description")
    description_value = str(description_raw) if description_raw else None

    try:
        data = ExpenseForm.model_validate(
            {
                "amount": amount_raw,
                "category_id": category_id_raw,
                "date": date_raw,
                "description": description_value,
            }
        )
    except ValidationError as exc:
        errors = {str(err["loc"][0]): err["msg"] for err in exc.errors()}
        return await _render_expense_form(request, db, errors, amount_raw, category_id_raw, description_value)

    category = await db.get(Category, data.category_id)
    if category is None:
        return await _render_expense_form(
            request, db, {"category_id": "Select a valid category."}, amount_raw, category_id_raw, description_value
        )

    expense = Expense(
        user_id=current_user.id,
        category_id=data.category_id,
        amount=data.amount,
        date=data.date,
        description=data.description,
    )
    db.add(expense)
    await db.commit()

    return RedirectResponse(url="/expenses", status_code=302)
