import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.models import Vehicle, Sale, VehicleStatus, PaymentStatus
from app.database import Base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker


@pytest.mark.asyncio
async def test_webhook_payment_confirmed(override_dependencies, mock_vehicle_client):
    """Testa webhook de confirmação de pagamento"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Primeiro cria uma venda
        sale_data = {
            "vehicle_id": 1,
            "cpf_comprador": "52998224725"
        }
        sale_response = await ac.post("/api/v1/sales/", json=sale_data)
        assert sale_response.status_code == 201
        codigo_pagamento = sale_response.json()["codigo_pagamento"]
        
        # Confirma o pagamento via webhook
        webhook_data = {
            "codigo_pagamento": codigo_pagamento,
            "status": "CONFIRMADO"
        }
        response = await ac.post("/webhook/pagamento", json=webhook_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status_pagamento"] == "CONFIRMADO"
        assert "confirmado" in data["message"].lower()


@pytest.mark.asyncio
async def test_webhook_payment_cancelled(override_dependencies, mock_vehicle_client):
    """Testa webhook de cancelamento de pagamento"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Primeiro cria uma venda
        sale_data = {
            "vehicle_id": 1,
            "cpf_comprador": "52998224725"
        }
        sale_response = await ac.post("/api/v1/sales/", json=sale_data)
        assert sale_response.status_code == 201
        codigo_pagamento = sale_response.json()["codigo_pagamento"]
        
        # Cancela o pagamento via webhook
        webhook_data = {
            "codigo_pagamento": codigo_pagamento,
            "status": "CANCELADO"
        }
        response = await ac.post("/webhook/pagamento", json=webhook_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status_pagamento"] == "CANCELADO"
        assert data["vehicle_status"] == "DISPONIVEL"


@pytest.mark.asyncio
async def test_webhook_payment_not_found(override_dependencies):
    """Testa webhook com código de pagamento inexistente"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        webhook_data = {
            "codigo_pagamento": "codigo-inexistente",
            "status": "CONFIRMADO"
        }
        response = await ac.post("/webhook/pagamento", json=webhook_data)
        assert response.status_code == 404
        assert "não encontrado" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_webhook_payment_already_processed(override_dependencies, mock_vehicle_client):
    """Testa webhook com pagamento já processado"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Primeiro cria uma venda
        sale_data = {
            "vehicle_id": 1,
            "cpf_comprador": "52998224725"
        }
        sale_response = await ac.post("/api/v1/sales/", json=sale_data)
        codigo_pagamento = sale_response.json()["codigo_pagamento"]
        
        # Confirma o pagamento
        webhook_data = {
            "codigo_pagamento": codigo_pagamento,
            "status": "CONFIRMADO"
        }
        await ac.post("/webhook/pagamento", json=webhook_data)
        
        # Tenta confirmar novamente
        response = await ac.post("/webhook/pagamento", json=webhook_data)
        assert response.status_code == 400
        assert "já processado" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_webhook_invalid_status(override_dependencies):
    """Testa webhook com status inválido"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        webhook_data = {
            "codigo_pagamento": "algum-codigo",
            "status": "STATUS_INVALIDO"
        }
        response = await ac.post("/webhook/pagamento", json=webhook_data)
        assert response.status_code == 422  # Validation error
