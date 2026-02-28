import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
from app.main import app
from app.models.models import Vehicle, VehicleStatus
from app.services.sale_service import VehicleService
from app.database import Base, get_db
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.mark.asyncio
async def test_list_available_vehicles_with_data(override_dependencies, mock_vehicle_client):
    """Testa listagem de veículos disponíveis após criar venda"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Cria uma venda para popular o cache de veículos
        sale_data = {
            "vehicle_id": 1,
            "cpf_comprador": "52998224725"
        }
        await ac.post("/api/v1/sales/", json=sale_data)
        
        # O veículo agora está no cache como VENDIDO
        response = await ac.get("/api/v1/vehicles/available")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_sold_vehicles_after_sale(override_dependencies, mock_vehicle_client):
    """Testa listagem de veículos vendidos após criar venda"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Cria uma venda
        sale_data = {
            "vehicle_id": 1,
            "cpf_comprador": "52998224725"
        }
        await ac.post("/api/v1/sales/", json=sale_data)
        
        # Verifica veículos vendidos
        response = await ac.get("/api/v1/vehicles/sold")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "VENDIDO"


@pytest.mark.asyncio
async def test_vehicles_ordered_by_price(override_dependencies):
    """Testa que veículos são ordenados por preço"""
    with patch('app.services.sale_service.vehicle_client') as mock:
        # Mock para retornar veículos com preços diferentes
        call_count = [0]
        prices = [150000.00, 80000.00, 120000.00]
        
        async def mock_get_vehicle(vehicle_id):
            price = prices[call_count[0] % len(prices)]
            call_count[0] += 1
            return {
                "id": vehicle_id,
                "marca": "Marca",
                "modelo": "Modelo",
                "ano": 2023,
                "cor": "Cor",
                "preco": price,
                "status": "DISPONIVEL",
                "data_cadastro": "2024-01-01T00:00:00"
            }
        
        mock.get_vehicle = AsyncMock(side_effect=mock_get_vehicle)
        mock.update_vehicle_status = AsyncMock(return_value=True)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # Cria várias vendas
            cpfs = ["52998224725", "71168849040", "85365839004"]
            for i, cpf in enumerate(cpfs):
                sale_data = {"vehicle_id": i + 1, "cpf_comprador": cpf}
                await ac.post("/api/v1/sales/", json=sale_data)
            
            # Verifica ordenação
            response = await ac.get("/api/v1/vehicles/sold")
            assert response.status_code == 200
            data = response.json()
            
            # Verifica que os preços estão em ordem crescente
            if len(data) > 1:
                for i in range(len(data) - 1):
                    assert data[i]["preco"] <= data[i + 1]["preco"]
