from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select

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


async def test_summary_totals(client, db_session):
    user = await _create_logged_in_user(client, db_session, "summary-user@example.com")
    food_id = await _get_category_id(db_session, "Food")
    transport_id = await _get_category_id(db_session, "Transportation")

    today = date.today()
    db_session.add_all([
        Expense(user_id=user.id, category_id=food_id, amount=Decimal("10.00"), date=today),
        Expense(user_id=user.id, category_id=food_id, amount=Decimal("5.50"), date=today),
        Expense(user_id=user.id, category_id=transport_id, amount=Decimal("20.00"), date=today),
    ])
    await db_session.commit()

    response = await client.get("/summary")

    assert response.status_code == 200
    assert "15.50" in response.text
    assert "20.00" in response.text


async def test_summary_month_switch(client, db_session):
    user = await _create_logged_in_user(client, db_session, "summary-month@example.com")
    food_id = await _get_category_id(db_session, "Food")

    today = date.today()
    last_day_prev_month = today.replace(day=1) - timedelta(days=1)

    db_session.add(
        Expense(user_id=user.id, category_id=food_id, amount=Decimal("50.00"), date=last_day_prev_month)
    )
    await db_session.commit()

    current_month_response = await client.get("/summary")
    assert current_month_response.status_code == 200
    assert "50.00" not in current_month_response.text

    past_month_str = last_day_prev_month.strftime("%Y-%m")
    past_month_response = await client.get(f"/summary?month={past_month_str}")
    assert past_month_response.status_code == 200
    assert "50.00" in past_month_response.text


async def test_summary_empty_month(client, db_session):
    await _create_logged_in_user(client, db_session, "summary-empty@example.com")

    response = await client.get("/summary")

    assert response.status_code == 200
    assert "no expenses" in response.text.lower() or "haven't recorded" in response.text.lower()


async def test_summary_isolation(client, db_session):
    owner = await _create_logged_in_user(client, db_session, "summary-owner@example.com")
    food_id = await _get_category_id(db_session, "Food")

    other = User(email="summary-other@example.com", password_hash=hash_password("Password1"))
    db_session.add(other)
    await db_session.commit()
    await db_session.refresh(other)

    today = date.today()
    db_session.add_all([
        Expense(user_id=owner.id, category_id=food_id, amount=Decimal("10.00"), date=today),
        Expense(user_id=other.id, category_id=food_id, amount=Decimal("999.00"), date=today),
    ])
    await db_session.commit()

    response = await client.get("/summary")

    assert response.status_code == 200
    assert "10.00" in response.text
    assert "999.00" not in response.text
