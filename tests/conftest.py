import pytest
import pytest_asyncio
import asyncio
from unittest.mock import patch, AsyncMock
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.database import Base, get_db
from app.main import app


# Criar engine de teste em memória
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Cria uma sessão de banco de dados para testes"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def override_dependencies(db_session):
    """Sobrescreve as dependências do FastAPI para usar o banco de teste"""
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def event_loop():
    """Cria um event loop para toda a sessão de testes"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Mock para vehicle_client
@pytest.fixture
def mock_vehicle_client():
    """Mock do cliente HTTP para o serviço de veículos"""
    with patch('app.services.sale_service.vehicle_client') as mock:
        mock.get_vehicle = AsyncMock(return_value={
            "id": 1,
            "marca": "Toyota",
            "modelo": "Corolla",
            "ano": 2023,
            "cor": "Preto",
            "preco": 95000.00,
            "status": "DISPONIVEL",
            "data_cadastro": "2024-01-01T00:00:00"
        })
        mock.update_vehicle_status = AsyncMock(return_value=True)
        yield mock
