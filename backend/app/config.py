from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "CrossSell IQ"
    VERSION: str = "2.1.0"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    
    DATABASE_URL: str = "sqlite+aiosqlite:///./crosssell.db"
    DATABASE_URL_SYNC: str = "sqlite:///./crosssell.db"
    
    REDIS_URL: Optional[str] = None
    
    SECRET_KEY: str = "dev-secret-key-change-in-production-min-32-chars!!"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    ALLOWED_ORIGINS: list = ["*"]
    
    LOG_LEVEL: str = "INFO"
    RATE_LIMIT_PER_MINUTE: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()
