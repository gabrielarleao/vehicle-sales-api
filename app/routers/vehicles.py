from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.schemas.schemas import VehicleResponse
from app.services.sale_service import VehicleService
from app.models.models import VehicleStatus

router = APIRouter()


@router.get("/available", response_model=List[VehicleResponse])
async def list_available_vehicles(db: AsyncSession = Depends(get_db)):
    """
    Lista veículos disponíveis para venda.
    
    Retorna veículos com status DISPONIVEL, ordenados por preço
    do mais barato para o mais caro.
    """
    service = VehicleService(db)
    return await service.get_available_vehicles()


@router.get("/sold", response_model=List[VehicleResponse])
async def list_sold_vehicles(db: AsyncSession = Depends(get_db)):
    """
    Lista veículos vendidos.
    
    Retorna veículos com status VENDIDO, ordenados por preço
    do mais barato para o mais caro.
    """
    service = VehicleService(db)
    return await service.get_sold_vehicles()
