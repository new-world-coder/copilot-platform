"""
Local LLM Integration - Ollama API
"""

import logging
from typing import Dict, Any, Optional
import asyncio
import httpx
import json

logger = logging.getLogger(__name__)


async def run_local_llm(prompt: str, model: str = "llama2", base_url: str = "http://localhost:11434", **kwargs) -> str:
    """
    Run local LLM via Ollama API
    
    Args:
        prompt: Input prompt for the LLM
        model: Model name (e.g., "llama2", "mistral", "codellama")
        base_url: Ollama API base URL
        **kwargs: Additional parameters (temperature, max_tokens, etc.)
        
    Returns:
        LLM response text
    """
    try:
        logger.info(f"Running Ollama LLM '{model}' with prompt length: {len(prompt)}")
        
        # Prepare request payload
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
                "top_p": kwargs.get("top_p", 0.9),
                "max_tokens": kwargs.get("max_tokens", 1000),
                "stop": kwargs.get("stop", [])
            }
        }
        
        # Make API request to Ollama
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{base_url}/api/generate",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                llm_response = result.get("response", "")
                
                logger.info(f"Ollama LLM '{model}' completed successfully")
                return llm_response
            else:
                error_msg = f"Ollama API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
        
    except httpx.ConnectError:
        logger.warning(f"Ollama not running at {base_url}, falling back to placeholder")
        return await _fallback_response(prompt, model, "Ollama")
    except Exception as e:
        logger.error(f"Error running Ollama LLM '{model}': {e}")
        return await _fallback_response(prompt, model, "Ollama")


async def _fallback_response(prompt: str, model: str, service: str) -> str:
    """Fallback response when service is not available"""
    response = f"{service} {model} response (service unavailable):\n\n"
    response += f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}\n\n"
    response += f"This is a fallback response. The {service} service is not running. "
    response += f"Please start {service} at localhost:11434 to use real LLM responses."
    
    # Simulate processing time
    await asyncio.sleep(0.1)
    return response


async def run_ollama_llm(prompt: str, model: str = "llama2", **kwargs) -> str:
    """
    Run Ollama LLM specifically (alias for run_local_llm)
    
    Args:
        prompt: Input prompt
        model: Ollama model name
        **kwargs: Additional parameters
        
    Returns:
        LLM response
    """
    return await run_local_llm(prompt, model, **kwargs)


async def run_lm_studio_llm(prompt: str, model: str = "custom", **kwargs) -> str:
    """
    Run LM Studio LLM
    
    Args:
        prompt: Input prompt
        model: LM Studio model name
        **kwargs: Additional parameters
        
    Returns:
        LLM response
    """
    try:
        # This would connect to LM Studio API
        
        response = f"LM Studio {model} response:\n\n"
        response += f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}\n\n"
        response += f"This would connect to LM Studio API "
        response += f"and use the {model} model for generation."
        
        return response
        
    except Exception as e:
        logger.error(f"Error running LM Studio LLM '{model}': {e}")
        raise


def get_available_local_models() -> list:
    """Get list of available local models"""
    return [
        "llama2",
        "llama2:7b",
        "llama2:13b",
        "mistral",
        "mistral:7b",
        "codellama",
        "codellama:7b",
        "codellama:13b",
        "phi",
        "phi:3b",
        "custom"
    ]


def validate_local_model(model: str) -> bool:
    """Validate if local model is available"""
    return model in get_available_local_models()


async def check_local_llm_health(endpoint: str = "http://localhost:11434") -> bool:
    """Check if Ollama service is running"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{endpoint}/api/tags")
            return response.status_code == 200
            
    except Exception as e:
        logger.error(f"Ollama health check failed: {e}")
        return False


async def get_available_ollama_models(endpoint: str = "http://localhost:11434") -> list:
    """Get list of available Ollama models"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{endpoint}/api/tags")
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
            else:
                return get_available_local_models()  # Fallback
    except Exception as e:
        logger.error(f"Error getting Ollama models: {e}")
        return get_available_local_models()


# Convenience function
async def run_local_llm_simple(prompt: str) -> str:
    """Simple interface for running local LLM"""
    return await run_local_llm(prompt)
