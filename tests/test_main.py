import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    """Testa o endpoint de health check"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["service"] == "vehicle-sales-api"


@pytest.mark.asyncio
async def test_list_available_vehicles_empty(override_dependencies):
    """Testa listagem de veículos disponíveis quando vazia"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/vehicles/available")
        assert response.status_code == 200
        assert response.json() == []


@pytest.mark.asyncio
async def test_list_sold_vehicles_empty(override_dependencies):
    """Testa listagem de veículos vendidos quando vazia"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/vehicles/sold")
        assert response.status_code == 200
        assert response.json() == []
