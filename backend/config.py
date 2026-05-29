# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    OLLAMA_BASE_URL: str
    OLLAMA_MODEL: str
    CHROMA_PERSIST_PATH: str
    MEDIA_SOURCE_PATH: str
    WHISPER_MODEL_SIZE: str
    DATABASE_URL: str
    APP_VERSION: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
