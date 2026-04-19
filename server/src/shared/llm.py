from langchain_core.language_models import BaseChatModel
from langchain_openai import AzureChatOpenAI

from src.shared.config import get_settings


def get_llm() -> BaseChatModel:
    settings = get_settings()
    return AzureChatOpenAI(
        azure_deployment=settings.azure_deployment,
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.api_version,
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )
