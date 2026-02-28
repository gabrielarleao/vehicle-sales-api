from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.schemas.schemas import SaleCreate, SaleResponse, PaymentWebhook, PaymentWebhookResponse
from app.services.sale_service import SaleService

router = APIRouter()


@router.post("/", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
async def create_sale(
    sale_in: SaleCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Efetua a venda de um veículo.
    
    - **vehicle_id**: ID do veículo no serviço principal
    - **cpf_comprador**: CPF do comprador (válido, 11 dígitos)
    
    Retorna a venda criada com código de pagamento único.
    O status inicial do pagamento é PENDENTE.
    
    A entidade processadora de pagamento deve usar o código de pagamento
    para confirmar ou cancelar via endpoint /webhook/pagamento.
    """
    service = SaleService(db)
    return await service.create_sale(sale_in)


@router.get("/", response_model=List[SaleResponse])
async def list_sales(db: AsyncSession = Depends(get_db)):
    """
    Lista todas as vendas registradas.
    """
    service = SaleService(db)
    return await service.get_sales()


@router.get("/{codigo_pagamento}", response_model=SaleResponse)
async def get_sale(
    codigo_pagamento: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Busca uma venda pelo código de pagamento.
    """
    service = SaleService(db)
    sale = await service.get_sale_by_codigo(codigo_pagamento)
    if not sale:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venda não encontrada"
        )
    return sale
