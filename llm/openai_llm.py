"""
OpenAI LLM Integration
"""

import logging
from typing import Dict, Any, Optional
import asyncio

logger = logging.getLogger(__name__)


async def run_openai_llm(prompt: str, api_key: str, model: str = "gpt-4", **kwargs) -> str:
    """
    Run OpenAI LLM
    
    Args:
        prompt: Input prompt for the LLM
        api_key: OpenAI API key
        model: Model name (gpt-4, gpt-3.5-turbo, etc.)
        **kwargs: Additional parameters (temperature, max_tokens, etc.)
        
    Returns:
        LLM response text
    """
    try:
        logger.info(f"Running OpenAI LLM '{model}' with prompt length: {len(prompt)}")
        
        # This would integrate with actual OpenAI API
        # For now, return placeholder response
        
        response = f"OpenAI placeholder response from {model}:\n\n"
        response += f"API Key: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else '***'}\n"
        response += f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}\n\n"
        response += f"This is a mock response from the OpenAI {model} model. "
        response += f"In a real implementation, this would make an API call to OpenAI "
        response += f"using the provided API key and return the generated response."
        
        # Simulate processing time
        await asyncio.sleep(0.1)
        
        logger.info(f"OpenAI LLM '{model}' completed successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error running OpenAI LLM '{model}': {e}")
        raise


async def run_gpt4(prompt: str, api_key: str, **kwargs) -> str:
    """
    Run GPT-4 specifically
    
    Args:
        prompt: Input prompt
        api_key: OpenAI API key
        **kwargs: Additional parameters
        
    Returns:
        LLM response
    """
    try:
        response = f"GPT-4 response:\n\n"
        response += f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}\n\n"
        response += f"This would use the GPT-4 model via OpenAI API "
        response += f"with the provided API key for generation."
        
        return response
        
    except Exception as e:
        logger.error(f"Error running GPT-4: {e}")
        raise


async def run_gpt35_turbo(prompt: str, api_key: str, **kwargs) -> str:
    """
    Run GPT-3.5 Turbo specifically
    
    Args:
        prompt: Input prompt
        api_key: OpenAI API key
        **kwargs: Additional parameters
        
    Returns:
        LLM response
    """
    try:
        response = f"GPT-3.5 Turbo response:\n\n"
        response += f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}\n\n"
        response += f"This would use the GPT-3.5 Turbo model via OpenAI API "
        response += f"with the provided API key for generation."
        
        return response
        
    except Exception as e:
        logger.error(f"Error running GPT-3.5 Turbo: {e}")
        raise


async def run_gpt4_turbo(prompt: str, api_key: str, **kwargs) -> str:
    """
    Run GPT-4 Turbo specifically
    
    Args:
        prompt: Input prompt
        api_key: OpenAI API key
        **kwargs: Additional parameters
        
    Returns:
        LLM response
    """
    try:
        response = f"GPT-4 Turbo response:\n\n"
        response += f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}\n\n"
        response += f"This would use the GPT-4 Turbo model via OpenAI API "
        response += f"with the provided API key for generation."
        
        return response
        
    except Exception as e:
        logger.error(f"Error running GPT-4 Turbo: {e}")
        raise


def get_available_openai_models() -> list:
    """Get list of available OpenAI models"""
    return [
        "gpt-4",
        "gpt-4-turbo",
        "gpt-4-turbo-preview",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k",
        "text-davinci-003",
        "text-davinci-002",
        "text-curie-001",
        "text-babbage-001",
        "text-ada-001"
    ]


def validate_openai_model(model: str) -> bool:
    """Validate if OpenAI model is available"""
    return model in get_available_openai_models()


def validate_api_key(api_key: str) -> bool:
    """Validate OpenAI API key format"""
    if not api_key:
        return False
    
    # Basic validation - OpenAI keys start with 'sk-'
    return api_key.startswith('sk-')


async def check_openai_health(api_key: str) -> bool:
    """Check if OpenAI API is accessible"""
    try:
        import httpx
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.openai.com/v1/models",
                headers=headers
            )
            return response.status_code == 200
            
    except Exception as e:
        logger.error(f"OpenAI health check failed: {e}")
        return False


async def get_openai_models(api_key: str) -> list:
    """Get available models from OpenAI API"""
    try:
        import httpx
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.openai.com/v1/models",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return [model["id"] for model in data.get("data", [])]
            else:
                return get_available_openai_models()  # Fallback
                
    except Exception as e:
        logger.error(f"Error getting OpenAI models: {e}")
        return get_available_openai_models()


# Convenience function
async def run_openai_llm_simple(prompt: str, api_key: str) -> str:
    """Simple interface for running OpenAI LLM"""
    return await run_openai_llm(prompt, api_key)
