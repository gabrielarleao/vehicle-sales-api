import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import asc
from fastapi import HTTPException, status
from datetime import datetime

from app.models.models import Sale, Vehicle, VehicleStatus, PaymentStatus
from app.schemas.schemas import SaleCreate, PaymentWebhook
from app.services.vehicle_client import vehicle_client


class VehicleService:
    """Serviço para gerenciamento de veículos (cache local)"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def sync_vehicle_from_principal(self, external_id: int) -> Vehicle | None:
        """
        Sincroniza um veículo do serviço principal para o cache local.
        
        Args:
            external_id: ID do veículo no serviço principal
            
        Returns:
            Vehicle local ou None se não encontrado no serviço principal
        """
        # Busca veículo no serviço principal via HTTP
        vehicle_data = await vehicle_client.get_vehicle(external_id)
        
        if not vehicle_data:
            return None
        
        # Verifica se já existe no cache local
        result = await self.db.execute(
            select(Vehicle).where(Vehicle.external_id == external_id)
        )
        local_vehicle = result.scalar_one_or_none()
        
        if local_vehicle:
            # Atualiza dados do cache
            local_vehicle.marca = vehicle_data["marca"]
            local_vehicle.modelo = vehicle_data["modelo"]
            local_vehicle.ano = vehicle_data["ano"]
            local_vehicle.cor = vehicle_data["cor"]
            local_vehicle.preco = vehicle_data["preco"]
            local_vehicle.status = VehicleStatus(vehicle_data["status"])
            local_vehicle.updated_at = datetime.utcnow()
        else:
            # Cria novo registro no cache
            local_vehicle = Vehicle(
                external_id=vehicle_data["id"],
                marca=vehicle_data["marca"],
                modelo=vehicle_data["modelo"],
                ano=vehicle_data["ano"],
                cor=vehicle_data["cor"],
                preco=vehicle_data["preco"],
                status=VehicleStatus(vehicle_data["status"]),
                data_cadastro=datetime.fromisoformat(
                    vehicle_data["data_cadastro"].replace("Z", "+00:00")
                ) if isinstance(vehicle_data["data_cadastro"], str) else vehicle_data["data_cadastro"]
            )
            self.db.add(local_vehicle)
        
        await self.db.commit()
        await self.db.refresh(local_vehicle)
        return local_vehicle
    
    async def get_available_vehicles(self) -> list[Vehicle]:
        """
        Retorna veículos disponíveis ordenados por preço (menor para maior).
        """
        result = await self.db.execute(
            select(Vehicle)
            .where(Vehicle.status == VehicleStatus.DISPONIVEL)
            .order_by(asc(Vehicle.preco))
        )
        return result.scalars().all()
    
    async def get_sold_vehicles(self) -> list[Vehicle]:
        """
        Retorna veículos vendidos ordenados por preço (menor para maior).
        """
        result = await self.db.execute(
            select(Vehicle)
            .where(Vehicle.status == VehicleStatus.VENDIDO)
            .order_by(asc(Vehicle.preco))
        )
        return result.scalars().all()
    
    async def get_vehicle_by_external_id(self, external_id: int) -> Vehicle | None:
        """Busca veículo pelo ID externo (do serviço principal)"""
        result = await self.db.execute(
            select(Vehicle).where(Vehicle.external_id == external_id)
        )
        return result.scalar_one_or_none()


class SaleService:
    """Serviço para gerenciamento de vendas"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.vehicle_service = VehicleService(db)
    
    async def create_sale(self, sale_in: SaleCreate) -> Sale:
        """
        Registra uma nova venda.
        
        Args:
            sale_in: Dados da venda (vehicle_id, cpf_comprador)
            
        Returns:
            Sale criada com código de pagamento
            
        Raises:
            HTTPException: Se veículo não encontrado ou indisponível
        """
        # 1. Sincroniza veículo do serviço principal
        vehicle = await self.vehicle_service.sync_vehicle_from_principal(
            sale_in.vehicle_id
        )
        
        if not vehicle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Veículo não encontrado no serviço principal"
            )
        
        # 2. Verifica disponibilidade
        if vehicle.status != VehicleStatus.DISPONIVEL:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Veículo não está disponível para venda"
            )
        
        # 3. Gera código único de pagamento
        codigo_pagamento = str(uuid.uuid4())
        
        # 4. Cria registro de venda
        sale = Sale(
            vehicle_id=vehicle.id,
            cpf_comprador=sale_in.cpf_comprador,
            codigo_pagamento=codigo_pagamento,
            status_pagamento=PaymentStatus.PENDENTE,
            valor_venda=vehicle.preco
        )
        self.db.add(sale)
        
        # 5. Atualiza status do veículo local para VENDIDO
        vehicle.status = VehicleStatus.VENDIDO
        
        # 6. Atualiza status no serviço principal via HTTP
        await vehicle_client.update_vehicle_status(
            sale_in.vehicle_id, 
            VehicleStatus.VENDIDO.value
        )
        
        try:
            await self.db.commit()
            await self.db.refresh(sale)
            return sale
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao registrar venda: {str(e)}"
            )
    
    async def process_payment_webhook(self, webhook_data: PaymentWebhook) -> dict:
        """
        Processa webhook de confirmação/cancelamento de pagamento.
        
        Args:
            webhook_data: Dados do webhook (codigo_pagamento, status)
            
        Returns:
            Resultado do processamento
            
        Raises:
            HTTPException: Se código de pagamento não encontrado
        """
        # 1. Busca venda pelo código de pagamento
        result = await self.db.execute(
            select(Sale).where(Sale.codigo_pagamento == webhook_data.codigo_pagamento)
        )
        sale = result.scalar_one_or_none()
        
        if not sale:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Código de pagamento não encontrado"
            )
        
        # 2. Verifica se já foi processado
        if sale.status_pagamento != PaymentStatus.PENDENTE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Pagamento já processado com status: {sale.status_pagamento.value}"
            )
        
        # 3. Atualiza status do pagamento
        sale.status_pagamento = webhook_data.status
        
        # 4. Busca veículo associado
        result = await self.db.execute(
            select(Vehicle).where(Vehicle.id == sale.vehicle_id)
        )
        vehicle = result.scalar_one_or_none()
        
        vehicle_status = None
        
        # 5. Se cancelado, reverte status do veículo
        if webhook_data.status == PaymentStatus.CANCELADO and vehicle:
            vehicle.status = VehicleStatus.DISPONIVEL
            vehicle_status = VehicleStatus.DISPONIVEL
            
            # Atualiza no serviço principal
            await vehicle_client.update_vehicle_status(
                vehicle.external_id,
                VehicleStatus.DISPONIVEL.value
            )
        elif webhook_data.status == PaymentStatus.CONFIRMADO:
            vehicle_status = VehicleStatus.VENDIDO
        
        try:
            await self.db.commit()
            return {
                "message": f"Pagamento {webhook_data.status.value.lower()} com sucesso",
                "codigo_pagamento": webhook_data.codigo_pagamento,
                "status_pagamento": webhook_data.status,
                "vehicle_status": vehicle_status
            }
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao processar webhook: {str(e)}"
            )
    
    async def get_sales(self) -> list[Sale]:
        """Retorna todas as vendas"""
        result = await self.db.execute(select(Sale))
        return result.scalars().all()
    
    async def get_sale_by_codigo(self, codigo_pagamento: str) -> Sale | None:
        """Busca venda pelo código de pagamento"""
        result = await self.db.execute(
            select(Sale).where(Sale.codigo_pagamento == codigo_pagamento)
        )
        return result.scalar_one_or_none()
