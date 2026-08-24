from fastapi import APIRouter

from src.api.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health")
def health_check() -> HealthResponse:
    return HealthResponse(status="healthy")
