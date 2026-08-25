.PHONY: install docker-start docker-start-build docker-stop docker-logs test test-cov lint fix format type-check check generate-migration apply-migration

LOCAL_DATABASE_URL := postgresql+psycopg2://postgres:postgres@localhost:5432/{{ project_db_name }}

install:
	poetry install
	poetry run pre-commit install
	poetry run pre-commit install --hook-type pre-push

docker-start:
	docker compose up -d

docker-start-build:
	docker compose up -d --build

docker-stop:
	docker compose down

docker-logs:
	docker compose logs -f

test:
	TEST_DATABASE_URL="$(LOCAL_DATABASE_URL)" poetry run pytest

test-cov:
	TEST_DATABASE_URL="$(LOCAL_DATABASE_URL)" poetry run pytest --cov=src --cov-report=html --cov-report=term

lint:
	poetry run ruff check .

fix:
	poetry run ruff check --fix .

format:
	poetry run ruff format .

type-check:
	poetry run mypy src tests

check:
	poetry run ruff format --check .
	poetry run ruff check .
	poetry run mypy src tests

generate-migration:
	@printf "Enter migration description: "; read desc; \
	DATABASE_URL="$(LOCAL_DATABASE_URL)" poetry run alembic revision --autogenerate -m "$$desc"

apply-migration:
	DATABASE_URL="$(LOCAL_DATABASE_URL)" poetry run alembic upgrade head
