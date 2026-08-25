.PHONY: setup install docker-start docker-start-build docker-stop docker-logs test test-cov validate-project lint fix format type-check check generate-migration apply-migration

LOCAL_DATABASE_URL := postgresql+psycopg2://postgres:postgres@localhost:5432/{{ project_db_name }}

setup:
	@git_root="$$(git rev-parse --show-toplevel 2>/dev/null || true)"; \
	project_root="$$(pwd -P)"; \
	if [ -z "$$git_root" ]; then \
		git init -b main; \
	elif [ "$$git_root" != "$$project_root" ]; then \
		echo "This project is inside another Git repository. Run 'make install' and manage hooks from the parent repository."; \
		exit 1; \
	fi
	$(MAKE) install
	poetry run pre-commit install
	poetry run pre-commit install --hook-type pre-push
	$(MAKE) validate-project

install:
	poetry install

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

validate-project:
	poetry run python -m tests.acceptance.run

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
