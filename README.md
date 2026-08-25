# {{ project_name }}

Layered FastAPI service generated from `fastapi-layered-template`.

## Requirements

- Python 3.12
- Poetry 2.4
- Docker Desktop

## Start with Docker

```bash
make docker-start-build
```

The API runs at `http://127.0.0.1:8000`. Verify it with:

```bash
curl http://127.0.0.1:8000/health
```

Stop the containers with:

```bash
make docker-stop
```

## Local development

Install the project and Git hooks:

```bash
make install
```

Start PostgreSQL and run the API locally:

```bash
docker compose up -d db
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/{{ project_db_name }} poetry run uvicorn src.main:app --reload
```

## Checks

```bash
make test
make check
```

## Database migrations

```bash
make generate-migration
make apply-migration
```

Alembic generates migrations in `alembic/versions`. Review every generated migration before applying it.

## Structure

```text
src/
├── api/            HTTP routes, schemas, middleware, and dependency wiring
├── domain/         Entities, types, and domain exceptions
├── persistence/    SQLAlchemy models, repositories, and database lifecycle
├── services/       Business logic and orchestration
└── main.py         FastAPI application entry point
```

Routes receive services, services receive repositories, and repositories receive a request-scoped database session.

## Generate another project

```bash
copier copy --vcs-ref=main https://github.com/aishajv/fastapi-layered-template.git ./my-project
```
