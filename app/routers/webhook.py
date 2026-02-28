from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.schemas import PaymentWebhook, PaymentWebhookResponse
from app.services.sale_service import SaleService

router = APIRouter()


@router.post("/pagamento", response_model=PaymentWebhookResponse)
async def payment_webhook(
    webhook_data: PaymentWebhook,
    db: AsyncSession = Depends(get_db)
):
    """
    Webhook para processamento de pagamento.
    
    Este endpoint é chamado pela entidade processadora de pagamento
    para informar se o pagamento foi confirmado ou cancelado.
    
    - **codigo_pagamento**: Código único do pagamento (UUID retornado na criação da venda)
    - **status**: CONFIRMADO ou CANCELADO
    
    Comportamento:
    - Se CONFIRMADO: A venda é finalizada
    - Se CANCELADO: O veículo volta ao status DISPONIVEL
    
    Este endpoint é idempotente para o mesmo código de pagamento e status.
    """
    service = SaleService(db)
    result = await service.process_payment_webhook(webhook_data)
    return PaymentWebhookResponse(**result)
