import os
from collections.abc import Generator

import pytest

from src.config import get_settings


@pytest.fixture(autouse=True)
def configure_test_database_url(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[None, None, None]:
    monkeypatch.setenv(
        "DATABASE_URL",
        os.environ.get(
            "TEST_DATABASE_URL",
            "postgresql+psycopg2://test:test@localhost:5432/test",
        ),
    )
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
