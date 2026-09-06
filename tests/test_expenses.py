from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select

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


async def _get_category_id(db_session, name: str = "Food") -> int:
    category = await db_session.scalar(select(Category).where(Category.name == name))
    assert category is not None
    return category.id


async def _expense_count(db_session, user_id) -> int:
    return await db_session.scalar(
        select(func.count()).select_from(Expense).where(Expense.user_id == user_id)
    )


async def test_add_expense_success(client, db_session):
    user = await _create_logged_in_user(client, db_session, "expense-user@example.com")
    category_id = await _get_category_id(db_session)

    response = await client.post(
        "/expenses",
        data={
            "amount": "42.50",
            "category_id": str(category_id),
            "date": date.today().isoformat(),
            "description": "Groceries",
        },
    )

    assert response.status_code == 302
    assert response.headers["location"] == "/expenses"

    expense = await db_session.scalar(select(Expense).where(Expense.user_id == user.id))
    assert expense is not None
    assert expense.amount == Decimal("42.50")
    assert expense.category_id == category_id
    assert expense.date == date.today()
    assert expense.description == "Groceries"


async def test_add_expense_invalid_amount(client, db_session):
    user = await _create_logged_in_user(client, db_session, "bad-amount@example.com")
    category_id = await _get_category_id(db_session)

    for amount in ("0", "-5", ""):
        response = await client.post(
            "/expenses",
            data={"amount": amount, "category_id": str(category_id), "date": date.today().isoformat()},
        )
        assert response.status_code == 200
        assert "amount" in response.text.lower()

    assert await _expense_count(db_session, user.id) == 0


async def test_add_expense_missing_category(client, db_session):
    user = await _create_logged_in_user(client, db_session, "no-category@example.com")

    response = await client.post(
        "/expenses",
        data={"amount": "20.00", "category_id": "", "date": date.today().isoformat()},
    )

    assert response.status_code == 200
    assert "category" in response.text.lower()
    assert await _expense_count(db_session, user.id) == 0


async def test_add_expense_invalid_date(client, db_session):
    user = await _create_logged_in_user(client, db_session, "bad-date@example.com")
    category_id = await _get_category_id(db_session)

    future = (date.today() + timedelta(days=1)).isoformat()
    past = (date.today() - timedelta(days=1)).isoformat()

    for bad_date in (future, past, "not-a-date"):
        response = await client.post(
            "/expenses",
            data={"amount": "10.00", "category_id": str(category_id), "date": bad_date},
        )
        assert response.status_code == 200
        assert "date" in response.text.lower()

    assert await _expense_count(db_session, user.id) == 0


async def test_add_expense_amount_truncation(client, db_session):
    user = await _create_logged_in_user(client, db_session, "truncate@example.com")
    category_id = await _get_category_id(db_session)

    response = await client.post(
        "/expenses",
        data={"amount": "12.345", "category_id": str(category_id), "date": date.today().isoformat()},
    )

    assert response.status_code == 302

    expense = await db_session.scalar(select(Expense).where(Expense.user_id == user.id))
    assert expense is not None
    assert expense.amount == Decimal("12.34")


async def test_list_expenses_order(client, db_session):
    user = await _create_logged_in_user(client, db_session, "order-user@example.com")
    category_id = await _get_category_id(db_session)

    oldest = Expense(
        user_id=user.id, category_id=category_id, amount=Decimal("10.00"),
        date=date.today() - timedelta(days=2), description="oldest-entry",
    )
    middle = Expense(
        user_id=user.id, category_id=category_id, amount=Decimal("20.00"),
        date=date.today() - timedelta(days=1), description="middle-entry",
    )
    today_earlier = Expense(
        user_id=user.id, category_id=category_id, amount=Decimal("30.00"),
        date=date.today(), description="today-earlier-entry",
        created_at=datetime.now(timezone.utc) - timedelta(minutes=5),
    )
    today_later = Expense(
        user_id=user.id, category_id=category_id, amount=Decimal("40.00"),
        date=date.today(), description="today-later-entry",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add_all([oldest, middle, today_earlier, today_later])
    await db_session.commit()

    response = await client.get("/expenses")
    assert response.status_code == 200

    text = response.text
    positions = [text.index(marker) for marker in (
        "today-later-entry", "today-earlier-entry", "middle-entry", "oldest-entry",
    )]
    assert positions == sorted(positions)


async def test_list_expenses_empty(client, db_session):
    await _create_logged_in_user(client, db_session, "empty-list@example.com")

    response = await client.get("/expenses")

    assert response.status_code == 200
    assert "no expenses" in response.text.lower() or "haven't recorded" in response.text.lower()


async def test_list_expenses_isolation(client, db_session):
    owner = await _create_logged_in_user(client, db_session, "owner@example.com")
    category_id = await _get_category_id(db_session)

    other_user = User(email="other@example.com", password_hash=hash_password("Password1"))
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)

    db_session.add_all([
        Expense(
            user_id=owner.id, category_id=category_id, amount=Decimal("15.00"),
            date=date.today(), description="owners-expense",
        ),
        Expense(
            user_id=other_user.id, category_id=category_id, amount=Decimal("99.00"),
            date=date.today(), description="other-users-expense",
        ),
    ])
    await db_session.commit()

    response = await client.get("/expenses")

    assert response.status_code == 200
    assert "owners-expense" in response.text
    assert "other-users-expense" not in response.text
