from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    UPLOAD_DESTINATION: str = "uploads"
    DATABASE_URL: str

settings = Settings()