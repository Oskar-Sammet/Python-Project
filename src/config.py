from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    UPLOAD_DESTINATION: str = "uploads"
    DATABASE_URL: str

    OLLAMA_URL: str
    VISION_LANGUAGE_MODEL: str
    VISION_LANGUAGE_PROMPT: str

    QDRANT_HOST: str
    QDRANT_PORT: int


settings = Settings()