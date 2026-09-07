FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.12.6 /uv /uvx /usr/local/bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-editable

COPY app ./app
RUN uv sync --frozen --no-editable


FROM builder AS test

COPY tests ./tests
RUN uv sync --frozen --no-editable --extra dev

COPY alembic ./alembic
COPY alembic.ini ./alembic.ini
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x entrypoint.sh

RUN groupadd --system app && useradd --system --gid app --home-dir /app --no-create-home app \
    && chown -R app:app /app

ENV PATH="/app/.venv/bin:$PATH"

USER app

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
CMD ["pytest"]


FROM python:3.12-slim AS final

WORKDIR /app

COPY --from=builder /app/.venv ./.venv

COPY pyproject.toml ./pyproject.toml
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x entrypoint.sh

RUN groupadd --system app && useradd --system --gid app --home-dir /app --no-create-home app \
    && chown -R app:app /app

ENV PATH="/app/.venv/bin:$PATH"

USER app

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
