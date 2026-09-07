import time
import uuid

from sqlalchemy import select

from app.models.user import User
from app.security.jwt import ACCESS_TOKEN_COOKIE_NAME, create_access_token
from app.security.passwords import hash_password


async def test_register_and_duplicate_email(client, db_session):
    response = await client.post(
        "/register",
        data={"email": "new-user@example.com", "password": "Password1"},
    )

    assert response.status_code == 302
    assert response.headers["location"] == "/expenses"
    assert ACCESS_TOKEN_COOKIE_NAME in response.cookies

    user = await db_session.scalar(select(User).where(User.email == "new-user@example.com"))
    assert user is not None

    duplicate_response = await client.post(
        "/register",
        data={"email": "new-user@example.com", "password": "Password2"},
    )

    assert duplicate_response.status_code == 200
    assert "already exists" in duplicate_response.text.lower()

    all_users = (
        await db_session.execute(select(User).where(User.email == "new-user@example.com"))
    ).scalars().all()
    assert len(all_users) == 1


async def test_register_weak_password(client, db_session):
    response = await client.post(
        "/register",
        data={"email": "weak-pw@example.com", "password": "short"},
    )

    assert response.status_code == 200
    assert "8 characters" in response.text or "password" in response.text.lower()

    user = await db_session.scalar(select(User).where(User.email == "weak-pw@example.com"))
    assert user is None


async def test_login_success_and_failure(client, db_session):
    db_session.add(User(email="login-user@example.com", password_hash=hash_password("Password1")))
    await db_session.commit()

    bad_response = await client.post(
        "/login",
        data={"email": "login-user@example.com", "password": "WrongPassword1"},
    )
    assert bad_response.status_code == 200
    assert "invalid" in bad_response.text.lower()
    assert ACCESS_TOKEN_COOKIE_NAME not in bad_response.cookies

    good_response = await client.post(
        "/login",
        data={"email": "login-user@example.com", "password": "Password1"},
    )
    assert good_response.status_code == 302
    assert good_response.headers["location"] == "/expenses"
    assert ACCESS_TOKEN_COOKIE_NAME in good_response.cookies


async def test_logout(client, db_session):
    user = User(email="logout-user@example.com", password_hash=hash_password("Password1"))
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(subject=str(user.id))
    client.cookies.set(ACCESS_TOKEN_COOKIE_NAME, token)

    response = await client.post("/logout")

    assert response.status_code == 302
    assert response.headers["location"] == "/login"

    set_cookie_header = response.headers.get("set-cookie", "")
    assert ACCESS_TOKEN_COOKIE_NAME in set_cookie_header
    assert ('Max-Age=0' in set_cookie_header) or ('max-age=0' in set_cookie_header.lower())


async def test_user_id_not_email(client, db_session):
    await client.post(
        "/register",
        data={"email": "id-check@example.com", "password": "Password1"},
    )

    user = await db_session.scalar(select(User).where(User.email == "id-check@example.com"))
    assert user is not None
    assert isinstance(user.id, uuid.UUID)
    assert str(user.id) != user.email


async def test_register_latency_budget(client, db_session):
    start = time.perf_counter()
    response = await client.post(
        "/register",
        data={"email": "latency-user@example.com", "password": "Password1"},
    )
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert response.status_code == 302
    assert elapsed_ms < 500, (
        f"POST /register took {elapsed_ms:.1f}ms, exceeding the 500ms budget (SC-001). "
        "This route hashes the password with bcrypt, so it gets the higher "
        "password-hashing-route budget rather than the 200ms default."
    )
