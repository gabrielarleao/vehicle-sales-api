import enum
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class VehicleStatus(str, enum.Enum):
    DISPONIVEL = "DISPONIVEL"
    VENDIDO = "VENDIDO"


class PaymentStatus(str, enum.Enum):
    PENDENTE = "PENDENTE"
    CONFIRMADO = "CONFIRMADO"
    CANCELADO = "CANCELADO"


class Vehicle(Base):
    """
    Cache local de veículos sincronizado do serviço principal.
    external_id é o ID do veículo no serviço principal.
    """
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(Integer, unique=True, index=True, nullable=False)
    marca = Column(String, index=True)
    modelo = Column(String, index=True)
    ano = Column(Integer)
    cor = Column(String)
    preco = Column(Float)
    status = Column(Enum(VehicleStatus), default=VehicleStatus.DISPONIVEL)
    data_cadastro = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sale = relationship("Sale", back_populates="vehicle", uselist=False)


class Sale(Base):
    """
    Registro de vendas com informações de pagamento.
    Inclui CPF do comprador e status do pagamento via webhook.
    """
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), unique=True)
    cpf_comprador = Column(String(14), nullable=False, index=True)
    codigo_pagamento = Column(String(36), unique=True, nullable=False, index=True)
    status_pagamento = Column(Enum(PaymentStatus), default=PaymentStatus.PENDENTE)
    data_venda = Column(DateTime, default=datetime.utcnow)
    valor_venda = Column(Float)

    vehicle = relationship("Vehicle", back_populates="sale")
