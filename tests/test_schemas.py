import pytest
from app.schemas.schemas import SaleCreate


def test_valid_cpf():
    """Testa validação de CPF válido"""
    sale = SaleCreate(vehicle_id=1, cpf_comprador="52998224725")
    assert sale.cpf_comprador == "529.982.247-25"


def test_valid_cpf_formatted():
    """Testa validação de CPF válido já formatado"""
    sale = SaleCreate(vehicle_id=1, cpf_comprador="529.982.247-25")
    assert sale.cpf_comprador == "529.982.247-25"


def test_invalid_cpf_all_same_digits():
    """Testa rejeição de CPF com todos dígitos iguais"""
    with pytest.raises(ValueError):
        SaleCreate(vehicle_id=1, cpf_comprador="11111111111")


def test_invalid_cpf_wrong_check_digit():
    """Testa rejeição de CPF com dígito verificador errado"""
    with pytest.raises(ValueError):
        SaleCreate(vehicle_id=1, cpf_comprador="12345678900")


def test_invalid_cpf_too_short():
    """Testa rejeição de CPF muito curto"""
    with pytest.raises(ValueError):
        SaleCreate(vehicle_id=1, cpf_comprador="1234567890")


def test_invalid_cpf_too_long():
    """Testa rejeição de CPF muito longo"""
    with pytest.raises(ValueError):
        SaleCreate(vehicle_id=1, cpf_comprador="123456789012345")
