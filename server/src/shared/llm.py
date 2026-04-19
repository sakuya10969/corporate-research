from azure.identity import ClientSecretCredential
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

from src.shared.config import get_settings


def get_llm() -> BaseChatModel:
    settings = get_settings()
    credential = ClientSecretCredential(
        tenant_id=settings.tenant_id,
        client_id=settings.client_id,
        client_secret=settings.client_secret,
    )
    return init_chat_model(
        f"azure_ai:{settings.llm_model_name}",
        project_endpoint=settings.azure_ai_project_endpoint,
        credential=credential,
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )
