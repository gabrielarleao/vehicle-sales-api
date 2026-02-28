from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "Vehicle Sales API"
    API_V1_STR: str = "/api/v1"
    
    # Banco de dados de vendas (segregado)
    DATABASE_URL: str = "sqlite+aiosqlite:///./sales.db"
    
    # URL do serviço de veículos para comunicação HTTP
    VEHICLE_SERVICE_URL: str = "http://localhost:8000"
    
    # Chave secreta para validação de webhooks
    SECRET_KEY: str = "development-secret-key"
    WEBHOOK_SECRET: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
