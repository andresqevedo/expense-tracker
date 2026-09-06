from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.models.budget import Budget
from app.models.category import Category
from app.models.expense import Expense
from app.models.user import User
from app.security.jwt import ACCESS_TOKEN_COOKIE_NAME, create_access_token
from app.security.passwords import hash_password


async def _create_logged_in_user(client, db_session, email: str) -> User:
    user = User(email=email, password_hash=hash_password("Password1"))
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(subject=str(user.id))
    client.cookies.set(ACCESS_TOKEN_COOKIE_NAME, token)
    return user


async def _get_category_id(db_session, name: str) -> int:
    category = await db_session.scalar(select(Category).where(Category.name == name))
    assert category is not None
    return category.id


async def test_set_budget(client, db_session):
    user = await _create_logged_in_user(client, db_session, "budget-set@example.com")
    food_id = await _get_category_id(db_session, "Food")

    response = await client.post("/budgets", data={"category_id": str(food_id), "amount": "100.00"})

    assert response.status_code == 302
    assert response.headers["location"] == "/budgets"

    current_month = date.today().replace(day=1)
    budget = await db_session.scalar(
        select(Budget).where(
            Budget.user_id == user.id,
            Budget.category_id == food_id,
            Budget.effective_month == current_month,
        )
    )
    assert budget is not None
    assert budget.amount == Decimal("100.00")


async def test_budget_comparison(client, db_session):
    user = await _create_logged_in_user(client, db_session, "budget-compare@example.com")
    food_id = await _get_category_id(db_session, "Food")

    db_session.add(
        Budget(user_id=user.id, category_id=food_id, effective_month=date.today().replace(day=1), amount=Decimal("100.00"))
    )
    db_session.add(
        Expense(user_id=user.id, category_id=food_id, amount=Decimal("30.00"), date=date.today())
    )
    await db_session.commit()

    response = await client.get("/budgets")

    assert response.status_code == 200
    assert "100.00" in response.text
    assert "30.00" in response.text
    assert "70.00" in response.text
    assert "under" in response.text.lower()


async def test_budget_none_set(client, db_session):
    user = await _create_logged_in_user(client, db_session, "budget-none@example.com")
    food_id = await _get_category_id(db_session, "Food")

    db_session.add(
        Expense(user_id=user.id, category_id=food_id, amount=Decimal("15.00"), date=date.today())
    )
    await db_session.commit()

    response = await client.get("/budgets")

    assert response.status_code == 200
    assert "no budget set" in response.text.lower()


async def test_budget_update_same_month(client, db_session):
    user = await _create_logged_in_user(client, db_session, "budget-update@example.com")
    food_id = await _get_category_id(db_session, "Food")

    first = await client.post("/budgets", data={"category_id": str(food_id), "amount": "100.00"})
    assert first.status_code == 302
    second = await client.post("/budgets", data={"category_id": str(food_id), "amount": "150.00"})
    assert second.status_code == 302

    current_month = date.today().replace(day=1)
    result = await db_session.execute(
        select(Budget).where(
            Budget.user_id == user.id,
            Budget.category_id == food_id,
            Budget.effective_month == current_month,
        )
    )
    rows = result.scalars().all()
    assert len(rows) == 1
    assert rows[0].amount == Decimal("150.00")


async def test_budget_history_preserves_past_month(client, db_session):
    user = await _create_logged_in_user(client, db_session, "budget-history@example.com")
    food_id = await _get_category_id(db_session, "Food")

    today = date.today()
    current_month = today.replace(day=1)
    last_month_end = current_month - timedelta(days=1)
    past_month = last_month_end.replace(day=1)

    db_session.add(
        Budget(user_id=user.id, category_id=food_id, effective_month=past_month, amount=Decimal("50.00"))
    )
    await db_session.commit()

    response = await client.post("/budgets", data={"category_id": str(food_id), "amount": "200.00"})
    assert response.status_code == 302

    past_month_str = past_month.strftime("%Y-%m")
    past_response = await client.get(f"/budgets?month={past_month_str}")

    assert past_response.status_code == 200
    assert "50.00" in past_response.text


async def test_budget_amount_truncation(client, db_session):
    user = await _create_logged_in_user(client, db_session, "budget-truncate@example.com")
    food_id = await _get_category_id(db_session, "Food")

    response = await client.post("/budgets", data={"category_id": str(food_id), "amount": "12.345"})

    assert response.status_code == 302

    current_month = date.today().replace(day=1)
    budget = await db_session.scalar(
        select(Budget).where(
            Budget.user_id == user.id,
            Budget.category_id == food_id,
            Budget.effective_month == current_month,
        )
    )
    assert budget is not None
    assert budget.amount == Decimal("12.34")


async def test_budget_isolation(client, db_session):
    owner = await _create_logged_in_user(client, db_session, "budget-owner@example.com")
    food_id = await _get_category_id(db_session, "Food")

    other = User(email="budget-other@example.com", password_hash=hash_password("Password1"))
    db_session.add(other)
    await db_session.commit()
    await db_session.refresh(other)

    current_month = date.today().replace(day=1)
    db_session.add_all([
        Budget(user_id=owner.id, category_id=food_id, effective_month=current_month, amount=Decimal("100.00")),
        Budget(user_id=other.id, category_id=food_id, effective_month=current_month, amount=Decimal("999.00")),
        Expense(user_id=owner.id, category_id=food_id, amount=Decimal("10.00"), date=date.today()),
        Expense(user_id=other.id, category_id=food_id, amount=Decimal("888.00"), date=date.today()),
    ])
    await db_session.commit()

    response = await client.get("/budgets")

    assert response.status_code == 200
    assert "100.00" in response.text
    assert "10.00" in response.text
    assert "999.00" not in response.text
    assert "888.00" not in response.text
