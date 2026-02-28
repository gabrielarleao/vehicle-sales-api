"""
Testes para o cliente HTTP que comunica com o serviço de veículos.
"""
import pytest
import respx
from httpx import Response, RequestError
from app.services.vehicle_client import VehicleClient
from app.core.config import settings


@pytest.mark.asyncio
@respx.mock
async def test_vehicle_client_get_vehicle_success():
    """Testa busca de veículo com sucesso."""
    vehicle_data = {
        "id": 1,
        "marca": "Toyota",
        "modelo": "Corolla",
        "ano": 2022,
        "cor": "Prata",
        "preco": 120000.00,
        "status": "DISPONIVEL",
        "data_cadastro": "2024-01-01T00:00:00"
    }
    
    route = respx.get(f"{settings.VEHICLE_SERVICE_URL}/api/v1/vehicles/1").mock(
        return_value=Response(200, json=vehicle_data)
    )
    
    client = VehicleClient()
    result = await client.get_vehicle(1)
    
    assert route.called
    assert result is not None
    assert result["id"] == 1
    assert result["marca"] == "Toyota"


@pytest.mark.asyncio
@respx.mock
async def test_vehicle_client_get_vehicle_not_found():
    """Testa busca de veículo não encontrado."""
    route = respx.get(f"{settings.VEHICLE_SERVICE_URL}/api/v1/vehicles/999").mock(
        return_value=Response(404)
    )
    
    client = VehicleClient()
    result = await client.get_vehicle(999)
    
    assert route.called
    assert result is None


@pytest.mark.asyncio
@respx.mock
async def test_vehicle_client_get_vehicle_connection_error():
    """Testa erro de conexão ao buscar veículo."""
    route = respx.get(f"{settings.VEHICLE_SERVICE_URL}/api/v1/vehicles/1").mock(
        side_effect=RequestError("Connection failed")
    )
    
    client = VehicleClient()
    result = await client.get_vehicle(1)
    
    assert route.called
    assert result is None


@pytest.mark.asyncio
@respx.mock
async def test_vehicle_client_get_available_vehicles():
    """Testa listagem de veículos disponíveis."""
    vehicles = [
        {"id": 1, "marca": "Toyota", "preco": 95000, "status": "DISPONIVEL"},
        {"id": 2, "marca": "Honda", "preco": 85000, "status": "DISPONIVEL"}
    ]
    
    route = respx.get(f"{settings.VEHICLE_SERVICE_URL}/api/v1/vehicles/").mock(
        return_value=Response(200, json=vehicles)
    )
    
    client = VehicleClient()
    result = await client.get_available_vehicles()
    
    assert route.called
    assert len(result) == 2


@pytest.mark.asyncio
@respx.mock
async def test_vehicle_client_get_available_vehicles_error():
    """Testa erro ao listar veículos."""
    route = respx.get(f"{settings.VEHICLE_SERVICE_URL}/api/v1/vehicles/").mock(
        side_effect=RequestError("Connection failed")
    )
    
    client = VehicleClient()
    result = await client.get_available_vehicles()
    
    assert route.called
    assert result == []


@pytest.mark.asyncio
@respx.mock
async def test_vehicle_client_update_status_success():
    """Testa atualização de status com sucesso."""
    route = respx.put(f"{settings.VEHICLE_SERVICE_URL}/api/v1/vehicles/1").mock(
        return_value=Response(200)
    )
    
    client = VehicleClient()
    result = await client.update_vehicle_status(1, "VENDIDO")
    
    assert route.called
    assert result is True


@pytest.mark.asyncio
@respx.mock
async def test_vehicle_client_update_status_error():
    """Testa erro ao atualizar status."""
    route = respx.put(f"{settings.VEHICLE_SERVICE_URL}/api/v1/vehicles/1").mock(
        side_effect=RequestError("Connection failed")
    )
    
    client = VehicleClient()
    result = await client.update_vehicle_status(1, "VENDIDO")
    
    assert route.called
    assert result is False


@pytest.mark.asyncio
@respx.mock
async def test_vehicle_client_update_status_failure():
    """Testa falha (não 200) na atualização de status."""
    route = respx.put(f"{settings.VEHICLE_SERVICE_URL}/api/v1/vehicles/1").mock(
        return_value=Response(500)
    )
    
    client = VehicleClient()
    result = await client.update_vehicle_status(1, "VENDIDO")
    
    assert route.called
    assert result is False


def test_vehicle_client_config():
    """Testa configuração do cliente."""
    client = VehicleClient()
    assert client.base_url == settings.VEHICLE_SERVICE_URL
    assert client.timeout == 30.0
