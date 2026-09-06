from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse, Response
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.form_errors import field_errors
from app.models.user import User
from app.schemas.auth import LoginForm, RegisterForm
from app.security.jwt import ACCESS_TOKEN_COOKIE_NAME, ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token
from app.security.passwords import hash_password, verify_password
from app.templating import templates

router = APIRouter()

_GENERIC_LOGIN_ERROR = "Invalid email or password."


def _set_auth_cookie(response: Response, user_id: str) -> None:
    token = create_access_token(subject=user_id)
    response.set_cookie(
        ACCESS_TOKEN_COOKIE_NAME,
        token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/register")
async def register_form(request: Request):
    return templates.TemplateResponse(request=request, name="register.html", context={"errors": {}, "email": ""})


@router.post("/register")
async def register_submit(request: Request, db: AsyncSession = Depends(get_db)):
    form = await request.form()
    email_raw = str(form.get("email", ""))
    password_raw = str(form.get("password", ""))

    try:
        data = RegisterForm(email=email_raw, password=password_raw)
    except ValidationError as exc:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"errors": field_errors(exc), "email": email_raw},
        )

    existing = await db.scalar(select(User).where(User.email == data.email))
    if existing is not None:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "errors": {"email": "An account with that email already exists."},
                "email": email_raw,
            },
        )

    user = User(email=data.email, password_hash=hash_password(data.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)

    response = RedirectResponse(url="/expenses", status_code=302)
    _set_auth_cookie(response, str(user.id))
    return response


@router.get("/login")
async def login_form(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={"error": None, "email": ""})


@router.post("/login")
async def login_submit(request: Request, db: AsyncSession = Depends(get_db)):
    form = await request.form()
    email_raw = str(form.get("email", ""))
    password_raw = str(form.get("password", ""))

    data = LoginForm(email=email_raw, password=password_raw)

    user = await db.scalar(select(User).where(User.email == data.email.strip().lower()))
    if user is None or not verify_password(data.password, user.password_hash):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": _GENERIC_LOGIN_ERROR, "email": email_raw},
        )

    response = RedirectResponse(url="/expenses", status_code=302)
    _set_auth_cookie(response, str(user.id))
    return response


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(ACCESS_TOKEN_COOKIE_NAME)
    return response
