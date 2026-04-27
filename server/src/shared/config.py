from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    azure_openai_endpoint: str
    azure_openai_api_key: str
    azure_deployment: str
    api_version: str
    database_url: str = "postgresql+asyncpg://admin:password@localhost:5432/corporate-research"
    cors_origins: list[str] = ["http://localhost:3000"]
    clerk_issuer_url: str = ""
    clerk_jwks_url: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
