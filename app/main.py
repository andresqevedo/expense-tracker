from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.dependencies import NotAuthenticatedError
from app.routers import auth, budgets, expenses, summary
from app.templating import APP_DIR


def create_app() -> FastAPI:
    fastapi_app = FastAPI(title="Expense Tracker")

    fastapi_app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")

    @fastapi_app.exception_handler(NotAuthenticatedError)
    async def handle_not_authenticated(request: Request, exc: NotAuthenticatedError) -> RedirectResponse:
        return RedirectResponse(url="/login", status_code=303)

    fastapi_app.include_router(auth.router)
    fastapi_app.include_router(expenses.router)
    fastapi_app.include_router(summary.router)
    fastapi_app.include_router(budgets.router)

    return fastapi_app


app = create_app()
