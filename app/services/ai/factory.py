# app/services/ai/factory.py
from app.services.ai.base import BaseAIClient
from app.services.ai.claude_client import ClaudeClient
from app.services.ai.openai_client import OpenAIClient
from app.services.ai.ollama_client import OllamaClient
from app.core.config import settings


def create_ai_client(provider: str = None) -> BaseAIClient:
    name = (provider or settings.AI_PROVIDER).lower()
    if name == "claude":
        return ClaudeClient()
    elif name == "openai":
        return OpenAIClient()
    elif name == "ollama":
        return OllamaClient()
    raise ValueError(f"AI provider non supporte: {name}")
