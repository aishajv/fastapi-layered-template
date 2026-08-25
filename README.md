<p align="center">
  <img src="docs/assets/bootstrap-base-glow-hq.gif" alt="An engineer-scout activating a glowing modular software base camp" width="100%">
</p>

A layered FastAPI starter with PostgreSQL, SQLAlchemy, Alembic, Poetry, Docker, Ruff, MyPy, Pytest, and Git hooks.

## Requirements

- Python 3.12
- Poetry 2.4
- Git
- Make
- Copier 9 or later when creating a new project
- Docker Desktop

## Create a project

```bash
copier copy --vcs-ref=main https://github.com/aishajv/fastapi-layered-template.git ./my-project
cd my-project
make setup
```

`make setup` initializes Git when needed, installs the Poetry environment, and installs the commit and push hooks. Use `make install` when you only need to install dependencies.

## Run with Docker

```bash
make docker-start-build
curl http://127.0.0.1:8000/health
```

The API runs at `http://127.0.0.1:8000`. Stop the local stack with:

```bash
make docker-stop
```

## Run locally

Start PostgreSQL in Docker, then run the API through Poetry:

```bash
docker compose up -d db
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/{{ project_db_name }} poetry run uvicorn src.main:app --reload
```

## Common commands

| Command | Purpose |
| --- | --- |
| `make test` | Run the test suite |
| `make test-cov` | Run tests with coverage |
| `make check` | Check formatting, linting, and types |
| `make fix` | Apply safe Ruff lint fixes |
| `make docker-logs` | Follow local container logs |

## Database migrations

With PostgreSQL running:

```bash
make generate-migration
make apply-migration
```

Alembic writes migrations to `alembic/versions`. Review every generated migration before applying it.

## Architecture

```text
src/
├── api/            HTTP routes, schemas, middleware, and dependency wiring
├── domain/         Entities, types, and domain exceptions
├── persistence/    SQLAlchemy models, repositories, and database lifecycle
├── services/       Business logic and orchestration
└── main.py         FastAPI application entry point
```

Routes receive services, services receive repositories, and repositories receive a request-scoped database session.
