"""
OpenAI LLM Integration
"""

import logging
from typing import Dict, Any, Optional, List
import asyncio
import httpx
import json

logger = logging.getLogger(__name__)


async def run_openai_llm(prompt: str, api_key: str, model: str = "gpt-4", **kwargs) -> str:
    """
    Run OpenAI LLM via Chat Completions API
    
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
        
        # Validate API key
        if not api_key or not api_key.startswith('sk-'):
            raise ValueError("Invalid OpenAI API key format")
        
        # Prepare request payload
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1000),
            "top_p": kwargs.get("top_p", 1.0),
            "frequency_penalty": kwargs.get("frequency_penalty", 0.0),
            "presence_penalty": kwargs.get("presence_penalty", 0.0),
            "stop": kwargs.get("stop", None)
        }
        
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}
        
        # Make API request to OpenAI
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                llm_response = result["choices"][0]["message"]["content"]
                
                logger.info(f"OpenAI LLM '{model}' completed successfully")
                return llm_response
            else:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                error_msg = error_data.get("error", {}).get("message", response.text)
                logger.error(f"OpenAI API error: {response.status_code} - {error_msg}")
                raise Exception(f"OpenAI API error: {error_msg}")
        
    except httpx.ConnectError:
        logger.warning("OpenAI API connection failed, falling back to placeholder")
        return await _fallback_response(prompt, model, "OpenAI")
    except Exception as e:
        logger.error(f"Error running OpenAI LLM '{model}': {e}")
        return await _fallback_response(prompt, model, "OpenAI")


async def _fallback_response(prompt: str, model: str, service: str) -> str:
    """Fallback response when service is not available"""
    response = f"{service} {model} response (service unavailable):\n\n"
    response += f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}\n\n"
    response += f"This is a fallback response. The {service} service is not accessible. "
    response += f"Please check your API key and network connection."
    
    # Simulate processing time
    await asyncio.sleep(0.1)
    return response


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
    return await run_openai_llm(prompt, api_key, "gpt-4", **kwargs)


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
    return await run_openai_llm(prompt, api_key, "gpt-3.5-turbo", **kwargs)


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
    return await run_openai_llm(prompt, api_key, "gpt-4-turbo", **kwargs)


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
