# This module defines application settings loaded from the environment.
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Define all runtime configuration used by the application.
    BASE_BACKEND_URL: str

    GEMINI_API_KEY: str

    DENSE_EMBEDDING_BASE_URL: str

    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int

    LANGSMITH_TRACING: bool
    SECRET_API_KEY: str

    model_config = SettingsConfigDict(env_file_encoding="utf-8", env_file=".env")

settings = Settings()
