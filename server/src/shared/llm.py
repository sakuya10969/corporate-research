from azure.identity import DefaultAzureCredential
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

from src.shared.config import get_settings


def get_llm() -> BaseChatModel:
    settings = get_settings()
    return init_chat_model(
        f"azure_ai:{settings.llm_model_name}",
        project_endpoint=settings.azure_ai_project_endpoint,
        credential=DefaultAzureCredential(),
    )
