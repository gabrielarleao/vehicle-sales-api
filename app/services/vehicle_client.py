import httpx
from typing import Optional
from app.core.config import settings
from app.schemas.schemas import VehicleSync


class VehicleClient:
    """
    Cliente HTTP para comunicação com o serviço principal de veículos.
    Responsável por buscar e sincronizar dados de veículos.
    """
    
    def __init__(self):
        self.base_url = settings.VEHICLE_SERVICE_URL
        self.timeout = 30.0
    
    async def get_vehicle(self, vehicle_id: int) -> Optional[dict]:
        """
        Busca um veículo do serviço principal pelo ID.
        
        Args:
            vehicle_id: ID do veículo no serviço principal
            
        Returns:
            Dados do veículo ou None se não encontrado
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/vehicles/{vehicle_id}"
                )
                if response.status_code == 200:
                    return response.json()
                return None
            except httpx.RequestError as e:
                print(f"Erro ao conectar com serviço de veículos: {e}")
                return None
    
    async def get_available_vehicles(self) -> list[dict]:
        """
        Busca todos os veículos disponíveis do serviço principal.
        
        Returns:
            Lista de veículos disponíveis
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/vehicles/",
                    params={"status": "DISPONIVEL"}
                )
                if response.status_code == 200:
                    return response.json()
                return []
            except httpx.RequestError as e:
                print(f"Erro ao conectar com serviço de veículos: {e}")
                return []
    
    async def update_vehicle_status(self, vehicle_id: int, status: str) -> bool:
        """
        Atualiza o status de um veículo no serviço principal.
        
        Args:
            vehicle_id: ID do veículo
            status: Novo status (DISPONIVEL ou VENDIDO)
            
        Returns:
            True se atualização foi bem-sucedida
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.put(
                    f"{self.base_url}/api/v1/vehicles/{vehicle_id}",
                    json={"status": status}
                )
                return response.status_code == 200
            except httpx.RequestError as e:
                print(f"Erro ao atualizar veículo no serviço principal: {e}")
                return False


vehicle_client = VehicleClient()
