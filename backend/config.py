# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    OLLAMA_BASE_URL: str
    OLLAMA_MODEL: str
    CHROMA_PERSIST_PATH: str
    CHROMA_HOST: str
    CHROMA_PORT: int
    MEDIA_SOURCE_PATH: str
    WHISPER_MODEL_SIZE: str
    DATABASE_URL: str
    APP_VERSION: str
    REDIS_URL: str = "redis://localhost:6379/0"
    EMBEDDING_DIM: int = 1024
    VECTOR_DB_TYPE: str = "pgvector"

    model_config = SettingsConfigDict(
            env_file=[
                os.path.join(os.path.dirname(__file__), ".env"),
                os.path.join(os.path.dirname(__file__), "..", ".env")
            ],
            env_file_encoding="utf-8",
            extra="ignore"
        )
settings = Settings()
