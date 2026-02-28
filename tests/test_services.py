import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from datetime import datetime

from app.database import Base
from app.models.models import Vehicle, Sale, VehicleStatus, PaymentStatus
from app.schemas.schemas import SaleCreate, PaymentWebhook
from app.services.sale_service import VehicleService, SaleService


TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestSession() as session:
        yield session
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


MOCK_VEHICLE = {
    "id": 1,
    "marca": "Toyota",
    "modelo": "Corolla",
    "ano": 2023,
    "cor": "Preto",
    "preco": 95000.00,
    "status": "DISPONIVEL",
    "data_cadastro": "2024-01-01T00:00:00"
}

VALID_CPF = "529.982.247-25"


# --- VehicleService ---

@pytest.mark.asyncio
async def test_vehicle_service_sync_new(db):
    with patch('app.services.sale_service.vehicle_client') as mock:
        mock.get_vehicle = AsyncMock(return_value=MOCK_VEHICLE)
        svc = VehicleService(db)
        vehicle = await svc.sync_vehicle_from_principal(1)
        assert vehicle is not None
        assert vehicle.external_id == 1
        assert vehicle.marca == "Toyota"


@pytest.mark.asyncio
async def test_vehicle_service_sync_update_existing(db):
    with patch('app.services.sale_service.vehicle_client') as mock:
        mock.get_vehicle = AsyncMock(return_value=MOCK_VEHICLE)
        svc = VehicleService(db)
        await svc.sync_vehicle_from_principal(1)

        updated_data = {**MOCK_VEHICLE, "preco": 100000.00, "cor": "Branco"}
        mock.get_vehicle = AsyncMock(return_value=updated_data)
        vehicle = await svc.sync_vehicle_from_principal(1)
        assert vehicle.preco == 100000.00
        assert vehicle.cor == "Branco"


@pytest.mark.asyncio
async def test_vehicle_service_sync_not_found(db):
    with patch('app.services.sale_service.vehicle_client') as mock:
        mock.get_vehicle = AsyncMock(return_value=None)
        svc = VehicleService(db)
        result = await svc.sync_vehicle_from_principal(999)
        assert result is None


@pytest.mark.asyncio
async def test_vehicle_service_get_available(db):
    with patch('app.services.sale_service.vehicle_client') as mock:
        mock.get_vehicle = AsyncMock(return_value=MOCK_VEHICLE)
        svc = VehicleService(db)
        await svc.sync_vehicle_from_principal(1)
        available = await svc.get_available_vehicles()
        assert len(available) == 1


@pytest.mark.asyncio
async def test_vehicle_service_get_sold(db):
    svc = VehicleService(db)
    sold = await svc.get_sold_vehicles()
    assert len(sold) == 0


@pytest.mark.asyncio
async def test_vehicle_service_get_by_external_id(db):
    with patch('app.services.sale_service.vehicle_client') as mock:
        mock.get_vehicle = AsyncMock(return_value=MOCK_VEHICLE)
        svc = VehicleService(db)
        await svc.sync_vehicle_from_principal(1)
        found = await svc.get_vehicle_by_external_id(1)
        assert found is not None
        not_found = await svc.get_vehicle_by_external_id(999)
        assert not_found is None


# --- SaleService ---

@pytest.mark.asyncio
async def test_sale_service_create(db):
    with patch('app.services.sale_service.vehicle_client') as mock:
        mock.get_vehicle = AsyncMock(return_value=MOCK_VEHICLE)
        mock.update_vehicle_status = AsyncMock(return_value=True)
        svc = SaleService(db)
        sale = await svc.create_sale(SaleCreate(vehicle_id=1, cpf_comprador="52998224725"))
        assert sale.cpf_comprador == VALID_CPF
        assert sale.status_pagamento == PaymentStatus.PENDENTE
        assert sale.valor_venda == 95000.00


@pytest.mark.asyncio
async def test_sale_service_create_vehicle_not_found(db):
    with patch('app.services.sale_service.vehicle_client') as mock:
        mock.get_vehicle = AsyncMock(return_value=None)
        svc = SaleService(db)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            await svc.create_sale(SaleCreate(vehicle_id=999, cpf_comprador="52998224725"))
        assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_sale_service_create_vehicle_unavailable(db):
    sold_vehicle = {**MOCK_VEHICLE, "status": "VENDIDO"}
    with patch('app.services.sale_service.vehicle_client') as mock:
        mock.get_vehicle = AsyncMock(return_value=sold_vehicle)
        svc = SaleService(db)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            await svc.create_sale(SaleCreate(vehicle_id=1, cpf_comprador="52998224725"))
        assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_sale_service_webhook_confirm(db):
    with patch('app.services.sale_service.vehicle_client') as mock:
        mock.get_vehicle = AsyncMock(return_value=MOCK_VEHICLE)
        mock.update_vehicle_status = AsyncMock(return_value=True)
        svc = SaleService(db)
        sale = await svc.create_sale(SaleCreate(vehicle_id=1, cpf_comprador="52998224725"))

        result = await svc.process_payment_webhook(
            PaymentWebhook(codigo_pagamento=sale.codigo_pagamento, status=PaymentStatus.CONFIRMADO)
        )
        assert result["status_pagamento"] == PaymentStatus.CONFIRMADO
        assert result["vehicle_status"] == VehicleStatus.VENDIDO


@pytest.mark.asyncio
async def test_sale_service_webhook_cancel(db):
    with patch('app.services.sale_service.vehicle_client') as mock:
        mock.get_vehicle = AsyncMock(return_value=MOCK_VEHICLE)
        mock.update_vehicle_status = AsyncMock(return_value=True)
        svc = SaleService(db)
        sale = await svc.create_sale(SaleCreate(vehicle_id=1, cpf_comprador="52998224725"))

        result = await svc.process_payment_webhook(
            PaymentWebhook(codigo_pagamento=sale.codigo_pagamento, status=PaymentStatus.CANCELADO)
        )
        assert result["status_pagamento"] == PaymentStatus.CANCELADO
        assert result["vehicle_status"] == VehicleStatus.DISPONIVEL


@pytest.mark.asyncio
async def test_sale_service_webhook_not_found(db):
    svc = SaleService(db)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await svc.process_payment_webhook(
            PaymentWebhook(codigo_pagamento="inexistente", status=PaymentStatus.CONFIRMADO)
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_sale_service_webhook_already_processed(db):
    with patch('app.services.sale_service.vehicle_client') as mock:
        mock.get_vehicle = AsyncMock(return_value=MOCK_VEHICLE)
        mock.update_vehicle_status = AsyncMock(return_value=True)
        svc = SaleService(db)
        sale = await svc.create_sale(SaleCreate(vehicle_id=1, cpf_comprador="52998224725"))
        await svc.process_payment_webhook(
            PaymentWebhook(codigo_pagamento=sale.codigo_pagamento, status=PaymentStatus.CONFIRMADO)
        )
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            await svc.process_payment_webhook(
                PaymentWebhook(codigo_pagamento=sale.codigo_pagamento, status=PaymentStatus.CONFIRMADO)
            )
        assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_sale_service_get_sales(db):
    with patch('app.services.sale_service.vehicle_client') as mock:
        mock.get_vehicle = AsyncMock(return_value=MOCK_VEHICLE)
        mock.update_vehicle_status = AsyncMock(return_value=True)
        svc = SaleService(db)
        await svc.create_sale(SaleCreate(vehicle_id=1, cpf_comprador="52998224725"))
        sales = await svc.get_sales()
        assert len(sales) == 1


@pytest.mark.asyncio
async def test_sale_service_get_by_codigo(db):
    with patch('app.services.sale_service.vehicle_client') as mock:
        mock.get_vehicle = AsyncMock(return_value=MOCK_VEHICLE)
        mock.update_vehicle_status = AsyncMock(return_value=True)
        svc = SaleService(db)
        sale = await svc.create_sale(SaleCreate(vehicle_id=1, cpf_comprador="52998224725"))
        found = await svc.get_sale_by_codigo(sale.codigo_pagamento)
        assert found is not None
        not_found = await svc.get_sale_by_codigo("inexistente")
        assert not_found is None
