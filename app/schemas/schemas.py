from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from app.models.models import VehicleStatus, PaymentStatus
import re


class VehicleBase(BaseModel):
    marca: str
    modelo: str
    ano: int
    cor: str
    preco: float


class VehicleResponse(VehicleBase):
    id: int
    external_id: int
    status: VehicleStatus
    data_cadastro: datetime

    class Config:
        from_attributes = True


class VehicleSync(VehicleBase):
    """Schema para sincronização de veículo do serviço principal"""
    id: int
    status: VehicleStatus
    data_cadastro: datetime


class SaleCreate(BaseModel):
    vehicle_id: int = Field(..., description="ID do veículo no serviço principal")
    cpf_comprador: str = Field(..., min_length=11, max_length=14, description="CPF do comprador")
    
    @field_validator('cpf_comprador')
    @classmethod
    def validate_cpf(cls, v: str) -> str:
        # Remove caracteres não numéricos
        cpf_numbers = re.sub(r'\D', '', v)
        
        if len(cpf_numbers) != 11:
            raise ValueError('CPF deve conter 11 dígitos')
        
        # Verifica se todos os dígitos são iguais
        if cpf_numbers == cpf_numbers[0] * 11:
            raise ValueError('CPF inválido')
        
        # Validação do primeiro dígito verificador
        soma = sum(int(cpf_numbers[i]) * (10 - i) for i in range(9))
        resto = soma % 11
        digito1 = 0 if resto < 2 else 11 - resto
        
        if int(cpf_numbers[9]) != digito1:
            raise ValueError('CPF inválido')
        
        # Validação do segundo dígito verificador
        soma = sum(int(cpf_numbers[i]) * (11 - i) for i in range(10))
        resto = soma % 11
        digito2 = 0 if resto < 2 else 11 - resto
        
        if int(cpf_numbers[10]) != digito2:
            raise ValueError('CPF inválido')
        
        # Retorna CPF formatado
        return f"{cpf_numbers[:3]}.{cpf_numbers[3:6]}.{cpf_numbers[6:9]}-{cpf_numbers[9:]}"


class SaleResponse(BaseModel):
    id: int
    vehicle_id: int
    cpf_comprador: str
    codigo_pagamento: str
    status_pagamento: PaymentStatus
    data_venda: datetime
    valor_venda: float

    class Config:
        from_attributes = True


class PaymentWebhook(BaseModel):
    """Schema para webhook de confirmação de pagamento"""
    codigo_pagamento: str = Field(..., description="Código único do pagamento")
    status: PaymentStatus = Field(..., description="Status do pagamento: CONFIRMADO ou CANCELADO")


class PaymentWebhookResponse(BaseModel):
    message: str
    codigo_pagamento: str
    status_pagamento: PaymentStatus
    vehicle_status: Optional[VehicleStatus] = None
