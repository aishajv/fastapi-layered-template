from fastapi import APIRouter

from src.api.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", status_code=200)
def health_check() -> HealthResponse:
    return HealthResponse(status="healthy")
