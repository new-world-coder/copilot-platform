"""
Anthropic client for LLM interactions
"""

import anthropic
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class AnthropicClient:
    """Anthropic API client"""
    
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
    
    def chat_completion(self, messages: List[Dict[str, str]], 
                       temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Generate chat completion"""
        try:
            response = self.client.messages.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Error generating completion: {e}")
            raise
    
    def stream_completion(self, messages: List[Dict[str, str]], 
                         temperature: float = 0.7, max_tokens: int = 1000):
        """Stream chat completion"""
        try:
            response = self.client.messages.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            for chunk in response:
                if chunk.type == "content_block_delta":
                    yield chunk.delta.text
        except Exception as e:
            logger.error(f"Error streaming completion: {e}")
            raise
