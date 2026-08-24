from fastapi.testclient import TestClient

from src.api.schemas.health import HealthResponse
from src.main import app


def test_health_check_returns_healthy_response() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == HealthResponse(status="healthy").model_dump()
