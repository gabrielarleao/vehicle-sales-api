import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.models import Vehicle, VehicleStatus


@pytest.mark.asyncio
async def test_create_sale_success(override_dependencies, mock_vehicle_client):
    """Testa criação de venda com sucesso"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        sale_data = {
            "vehicle_id": 1,
            "cpf_comprador": "52998224725"  # CPF válido
        }
        response = await ac.post("/api/v1/sales/", json=sale_data)
        assert response.status_code == 201
        data = response.json()
        assert data["cpf_comprador"] == "529.982.247-25"
        assert data["status_pagamento"] == "PENDENTE"
        assert "codigo_pagamento" in data
        assert data["valor_venda"] == 95000.00


@pytest.mark.asyncio
async def test_create_sale_invalid_cpf(override_dependencies, mock_vehicle_client):
    """Testa criação de venda com CPF inválido"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        sale_data = {
            "vehicle_id": 1,
            "cpf_comprador": "11111111111"  # CPF inválido (todos dígitos iguais)
        }
        response = await ac.post("/api/v1/sales/", json=sale_data)
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_sale_vehicle_not_found(override_dependencies):
    """Testa criação de venda com veículo não encontrado"""
    with patch('app.services.sale_service.vehicle_client') as mock:
        mock.get_vehicle = AsyncMock(return_value=None)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            sale_data = {
                "vehicle_id": 999,
                "cpf_comprador": "52998224725"
            }
            response = await ac.post("/api/v1/sales/", json=sale_data)
            assert response.status_code == 404
            assert "não encontrado" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_sale_vehicle_unavailable(override_dependencies):
    """Testa criação de venda com veículo já vendido"""
    with patch('app.services.sale_service.vehicle_client') as mock:
        mock.get_vehicle = AsyncMock(return_value={
            "id": 1,
            "marca": "Toyota",
            "modelo": "Corolla",
            "ano": 2023,
            "cor": "Preto",
            "preco": 95000.00,
            "status": "VENDIDO",  # Veículo já vendido
            "data_cadastro": "2024-01-01T00:00:00"
        })
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            sale_data = {
                "vehicle_id": 1,
                "cpf_comprador": "52998224725"
            }
            response = await ac.post("/api/v1/sales/", json=sale_data)
            assert response.status_code == 400
            assert "não está disponível" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_sales_empty(override_dependencies):
    """Testa listagem de vendas quando vazia"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/sales/")
        assert response.status_code == 200
        assert response.json() == []


@pytest.mark.asyncio
async def test_get_sale_not_found(override_dependencies):
    """Testa busca de venda com código inexistente"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/sales/codigo-inexistente")
        assert response.status_code == 404
