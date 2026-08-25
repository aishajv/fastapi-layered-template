FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app \
    && pip install --no-cache-dir poetry==2.4.1

COPY pyproject.toml poetry.lock README.md ./

RUN poetry install --only main --no-interaction --no-ansi --no-root

COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./

RUN poetry install --only main --no-interaction --no-ansi

USER app

EXPOSE 8000

CMD ["sh", "-c", "poetry run uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
