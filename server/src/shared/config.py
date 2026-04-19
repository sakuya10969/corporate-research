from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    azure_ai_project_endpoint: str | None = None
    llm_model_name: str | None = None
    azure_openai_endpoint: str
    azure_openai_api_key: str
    azure_deployment: str
    api_version: str
    cors_origins: list[str] = ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
