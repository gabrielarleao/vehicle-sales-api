from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.config import settings
from app.routers import vehicles, sales, webhook
from app.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup: Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
    ## Serviço de Vendas de Veículos
    
    Este serviço é responsável por:
    
    - **Listagem de veículos** disponíveis e vendidos (ordenados por preço)
    - **Efetuar vendas** de veículos (com CPF do comprador)
    - **Webhook de pagamento** para confirmação/cancelamento
    
    ### Arquitetura
    
    Este serviço funciona de forma **isolada** com seu próprio banco de dados.
    A comunicação com o serviço principal de veículos é feita via **HTTP**.
    
    ### Fluxo de Venda
    
    1. Cliente chama `POST /api/v1/sales/` com `vehicle_id` e `cpf_comprador`
    2. Serviço sincroniza dados do veículo do serviço principal
    3. Cria registro de venda com `codigo_pagamento` único
    4. Entidade de pagamento processa e chama `POST /webhook/pagamento`
    5. Venda é confirmada ou cancelada baseado no status do pagamento
    """,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)


# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "vehicle-sales-api"}


# Include routers
app.include_router(
    vehicles.router,
    prefix=f"{settings.API_V1_STR}/vehicles",
    tags=["Veículos"]
)

app.include_router(
    sales.router,
    prefix=f"{settings.API_V1_STR}/sales",
    tags=["Vendas"]
)

app.include_router(
    webhook.router,
    prefix="/webhook",
    tags=["Webhook"]
)
