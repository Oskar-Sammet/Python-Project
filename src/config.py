from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    UPLOAD_DESTINATION: str = "uploads"
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 1800
    DATABASE_ECHO: bool = False

    OLLAMA_URL: str
    OLLAMA_MODEL: str
    OLLAMA_EMBEDDING_MODEL: str

    VISION_LANGUAGE_MODEL: str
    VISION_LANGUAGE_PROMPT: str

    QDRANT_HOST: str
    QDRANT_PORT: int

# Caching to avoid reading the .env file on every request
@lru_cache()
def get_settings() -> Settings:
    return Settings()