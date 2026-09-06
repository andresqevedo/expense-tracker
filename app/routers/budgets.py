from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.form_errors import field_errors
from app.models.budget import Budget
from app.models.category import Category
from app.models.expense import Expense
from app.models.user import User
from app.routers.summary import _month_start, _next_month_start
from app.schemas.budget import BudgetForm
from app.templating import templates

router = APIRouter()


async def _resolved_budgets(db: AsyncSession, user_id, month_start: date) -> dict[int, Decimal]:
    """For each category, the greatest effective_month <= month_start (data-model.md § Budget resolution rule)."""
    result = await db.execute(
        select(Budget.category_id, Budget.amount)
        .where(Budget.user_id == user_id, Budget.effective_month <= month_start)
        .order_by(Budget.category_id, Budget.effective_month.desc())
    )
    resolved: dict[int, Decimal] = {}
    for category_id, amount in result.all():
        resolved.setdefault(category_id, amount)
    return resolved


async def _actual_totals(db: AsyncSession, user_id, month_start: date, month_end: date) -> dict[int, Decimal]:
    result = await db.execute(
        select(Expense.category_id, func.sum(Expense.amount))
        .where(Expense.user_id == user_id, Expense.date >= month_start, Expense.date < month_end)
        .group_by(Expense.category_id)
    )
    return dict(result.all())


def _status(budgeted: Decimal | None, actual: Decimal) -> str:
    if budgeted is None:
        return "no_budget"
    if actual > budgeted:
        return "over"
    if actual < budgeted:
        return "under"
    return "on_budget"


@router.get("/budgets")
async def budget_comparison(
    request: Request,
    month: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    errors: dict[str, str] | None = None,
    form_category_id: str = "",
    form_amount: str = "",
):
    month_start = _month_start(month)
    month_end = _next_month_start(month_start)

    categories_result = await db.execute(select(Category).order_by(Category.name))
    categories = list(categories_result.scalars().all())

    resolved = await _resolved_budgets(db, current_user.id, month_start)
    actuals = await _actual_totals(db, current_user.id, month_start, month_end)

    rows = []
    for category in categories:
        budgeted = resolved.get(category.id)
        actual = actuals.get(category.id, Decimal("0.00"))
        if budgeted is None and actual == 0:
            continue
        difference = (budgeted - actual) if budgeted is not None else None
        rows.append(
            {
                "category": category,
                "budgeted": budgeted,
                "actual": actual,
                "difference": difference,
                "status": _status(budgeted, actual),
            }
        )

    return templates.TemplateResponse(
        request=request,
        name="budget.html",
        context={
            "rows": rows,
            "month": month_start.strftime("%Y-%m"),
            "categories": categories,
            "errors": errors or {},
            "form_category_id": form_category_id,
            "form_amount": form_amount,
        },
    )


@router.post("/budgets")
async def set_budget(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    form = await request.form()
    category_id_raw = str(form.get("category_id", ""))
    amount_raw = str(form.get("amount", ""))

    try:
        data = BudgetForm.model_validate({"category_id": category_id_raw, "amount": amount_raw})
    except ValidationError as exc:
        return await budget_comparison(
            request,
            None,
            current_user,
            db,
            errors=field_errors(exc),
            form_category_id=category_id_raw,
            form_amount=amount_raw,
        )

    category = await db.get(Category, data.category_id)
    if category is None:
        return await budget_comparison(
            request,
            None,
            current_user,
            db,
            errors={"category_id": "Select a valid category."},
            form_category_id=category_id_raw,
            form_amount=amount_raw,
        )

    current_month = datetime.now(timezone.utc).date().replace(day=1)
    existing = await db.scalar(
        select(Budget).where(
            Budget.user_id == current_user.id,
            Budget.category_id == data.category_id,
            Budget.effective_month == current_month,
        )
    )
    if existing is not None:
        existing.amount = data.amount
    else:
        db.add(
            Budget(
                user_id=current_user.id,
                category_id=data.category_id,
                effective_month=current_month,
                amount=data.amount,
            )
        )
    await db.commit()

    return RedirectResponse(url="/budgets", status_code=302)
