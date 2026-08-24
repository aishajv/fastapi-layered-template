FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir poetry==2.4.1

COPY pyproject.toml poetry.lock README.md ./

RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi --no-root

COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./

RUN poetry install --only main --no-interaction --no-ansi

EXPOSE 8000

CMD ["sh", "-c", "poetry run uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
