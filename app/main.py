from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.dependencies import NotAuthenticatedError

APP_DIR = Path(__file__).resolve().parent

templates = Jinja2Templates(directory=str(APP_DIR / "templates"))


def create_app() -> FastAPI:
    fastapi_app = FastAPI(title="Expense Tracker")

    fastapi_app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")

    @fastapi_app.exception_handler(NotAuthenticatedError)
    async def handle_not_authenticated(request: Request, exc: NotAuthenticatedError) -> RedirectResponse:
        return RedirectResponse(url="/login", status_code=303)

    # Routers are registered here as each user story's implementation phase adds them.

    return fastapi_app


app = create_app()
