from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routes.health import router as health_router
from src.config import get_settings
from src.persistence.database import Database


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    app.state.settings = settings
    app.state.db = Database(settings.DATABASE_URL)
    try:
        yield
    finally:
        app.state.db.engine.dispose()


app = FastAPI(title="{{ project_name }}", lifespan=lifespan)
app.include_router(health_router)
