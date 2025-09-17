"""
OpenAI client for LLM interactions
"""

import openai
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class OpenAIClient:
    """OpenAI API client"""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
    
    def chat_completion(self, messages: List[Dict[str, str]], 
                       temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Generate chat completion"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating completion: {e}")
            raise
    
    def stream_completion(self, messages: List[Dict[str, str]], 
                         temperature: float = 0.7, max_tokens: int = 1000):
        """Stream chat completion"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"Error streaming completion: {e}")
            raise
