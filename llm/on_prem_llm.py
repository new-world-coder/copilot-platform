"""
On-Premises LLM Integration
"""

import logging
from typing import Dict, Any, Optional
import asyncio
import httpx

logger = logging.getLogger(__name__)


async def run_on_prem_llm(prompt: str, endpoint: str, model: str = "custom-model", **kwargs) -> str:
    """
    Run on-premises LLM via configurable FastAPI endpoint
    
    Args:
        prompt: Input prompt for the LLM
        endpoint: On-premises LLM endpoint URL
        model: Model name
        **kwargs: Additional parameters (temperature, max_tokens, etc.)
        
    Returns:
        LLM response text
    """
    try:
        logger.info(f"Running on-prem LLM '{model}' at {endpoint}")
        
        # Validate endpoint
        if not endpoint or not endpoint.startswith(('http://', 'https://')):
            raise ValueError("Invalid endpoint URL")
        
        # Prepare request payload (OpenAI-compatible format)
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
        
        # Try OpenAI-compatible endpoint first
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{endpoint}/v1/chat/completions",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    llm_response = result["choices"][0]["message"]["content"]
                    logger.info(f"On-prem LLM '{model}' completed successfully")
                    return llm_response
                else:
                    logger.warning(f"OpenAI-compatible endpoint failed: {response.status_code}")
        except Exception as e:
            logger.warning(f"OpenAI-compatible endpoint failed: {e}")
        
        # Try alternative completion endpoint
        try:
            completion_payload = {
                "model": model,
                "prompt": prompt,
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 1000),
                "top_p": kwargs.get("top_p", 1.0),
                "stop": kwargs.get("stop", None)
            }
            completion_payload = {k: v for k, v in completion_payload.items() if v is not None}
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{endpoint}/v1/completions",
                    json=completion_payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    llm_response = result["choices"][0]["text"]
                    logger.info(f"On-prem LLM '{model}' completed successfully")
                    return llm_response
                else:
                    logger.warning(f"Completion endpoint failed: {response.status_code}")
        except Exception as e:
            logger.warning(f"Completion endpoint failed: {e}")
        
        # If all endpoints fail, return fallback response
        return await _fallback_response(prompt, model, endpoint)
        
    except Exception as e:
        logger.error(f"Error running on-prem LLM '{model}': {e}")
        return await _fallback_response(prompt, model, endpoint)


async def _fallback_response(prompt: str, model: str, endpoint: str) -> str:
    """Fallback response when service is not available"""
    response = f"On-Premises {model} response (service unavailable):\n\n"
    response += f"Endpoint: {endpoint}\n"
    response += f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}\n\n"
    response += f"This is a fallback response. The on-premises service at {endpoint} "
    response += f"is not accessible. Please check the endpoint URL and ensure the service is running."
    
    # Simulate processing time
    await asyncio.sleep(0.1)
    return response


async def run_vllm_llm(prompt: str, endpoint: str, model: str = "custom", **kwargs) -> str:
    """
    Run vLLM on-premises LLM (alias for run_on_prem_llm)
    
    Args:
        prompt: Input prompt
        endpoint: vLLM endpoint URL
        model: Model name
        **kwargs: Additional parameters
        
    Returns:
        LLM response
    """
    return await run_on_prem_llm(prompt, endpoint, model, **kwargs)


async def run_triton_llm(prompt: str, endpoint: str, model: str = "custom", **kwargs) -> str:
    """
    Run NVIDIA Triton Inference Server LLM (alias for run_on_prem_llm)
    
    Args:
        prompt: Input prompt
        endpoint: Triton endpoint URL
        model: Model name
        **kwargs: Additional parameters
        
    Returns:
        LLM response
    """
    return await run_on_prem_llm(prompt, endpoint, model, **kwargs)


async def run_custom_api_llm(prompt: str, endpoint: str, model: str = "custom", **kwargs) -> str:
    """
    Run custom API LLM (alias for run_on_prem_llm)
    
    Args:
        prompt: Input prompt
        endpoint: Custom API endpoint URL
        model: Model name
        **kwargs: Additional parameters
        
    Returns:
        LLM response
    """
    return await run_on_prem_llm(prompt, endpoint, model, **kwargs)


async def check_on_prem_health(endpoint: str) -> bool:
    """Check if on-premises LLM service is healthy"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Try health endpoint first
            try:
                response = await client.get(f"{endpoint}/health")
                if response.status_code == 200:
                    return True
            except:
                pass
            
            # Try models endpoint
            try:
                response = await client.get(f"{endpoint}/v1/models")
                return response.status_code == 200
            except:
                pass
            
            # Try root endpoint
            try:
                response = await client.get(endpoint)
                return response.status_code in [200, 404]  # 404 might be expected
            except:
                pass
            
            return False
            
    except Exception as e:
        logger.error(f"On-prem LLM health check failed for {endpoint}: {e}")
        return False


async def get_on_prem_models(endpoint: str) -> list:
    """Get available models from on-premises service"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{endpoint}/v1/models")
            
            if response.status_code == 200:
                data = response.json()
                return [model["id"] for model in data.get("data", [])]
            else:
                return ["custom-model-1", "custom-model-2"]  # Fallback
                
    except Exception as e:
        logger.error(f"Error getting on-prem models from {endpoint}: {e}")
        return ["custom-model-1", "custom-model-2"]


def validate_endpoint(endpoint: str) -> bool:
    """Validate on-premises endpoint URL"""
    try:
        from urllib.parse import urlparse
        result = urlparse(endpoint)
        return bool(result.scheme and result.netloc)
    except Exception:
        return False


# Convenience function
async def run_on_prem_llm_simple(prompt: str, endpoint: str) -> str:
    """Simple interface for running on-premises LLM"""
    return await run_on_prem_llm(prompt, endpoint)
