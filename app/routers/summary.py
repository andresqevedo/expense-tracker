from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.category import Category
from app.models.expense import Expense
from app.models.user import User
from app.templating import templates

router = APIRouter()


def _month_start(month: str | None) -> date:
    if month:
        try:
            year_str, month_str = month.split("-", 1)
            return date(int(year_str), int(month_str), 1)
        except (ValueError, TypeError):
            pass
    return datetime.now(timezone.utc).date().replace(day=1)


def _next_month_start(month_start: date) -> date:
    if month_start.month == 12:
        return date(month_start.year + 1, 1, 1)
    return date(month_start.year, month_start.month + 1, 1)


@router.get("/summary")
async def monthly_summary(
    request: Request,
    month: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    month_start = _month_start(month)
    month_end = _next_month_start(month_start)

    result = await db.execute(
        select(Category.name, func.sum(Expense.amount))
        .join(Expense, Expense.category_id == Category.id)
        .where(
            Expense.user_id == current_user.id,
            Expense.date >= month_start,
            Expense.date < month_end,
        )
        .group_by(Category.name)
        .order_by(Category.name)
    )
    totals = result.all()

    return templates.TemplateResponse(
        request=request,
        name="summary.html",
        context={"totals": totals, "month": month_start.strftime("%Y-%m")},
    )
