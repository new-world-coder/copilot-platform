"""
LLM factory for creating LLM clients
"""

from typing import Dict, Any, Optional
from .openai_client import OpenAIClient
from .anthropic_client import AnthropicClient

class LLMFactory:
    """Factory for creating LLM clients"""
    
    @staticmethod
    def create_client(provider: str, api_key: str, model: Optional[str] = None) -> Any:
        """Create LLM client based on provider"""
        if provider.lower() == "openai":
            return OpenAIClient(api_key=api_key, model=model or "gpt-4")
        elif provider.lower() == "anthropic":
            return AnthropicClient(api_key=api_key, model=model or "claude-3-sonnet-20240229")
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
