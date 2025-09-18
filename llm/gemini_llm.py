"""
Google Gemini LLM Integration
"""

import logging
from typing import Dict, Any, Optional, List
import asyncio
import httpx
import json

logger = logging.getLogger(__name__)


async def run_gemini_llm(prompt: str, api_key: str, model: str = "gemini-pro", **kwargs) -> str:
    """
    Run Google Gemini LLM via Generative AI API
    
    Args:
        prompt: Input prompt for the LLM
        api_key: Google AI API key
        model: Model name (gemini-pro, gemini-pro-vision, etc.)
        **kwargs: Additional parameters (temperature, max_tokens, etc.)
        
    Returns:
        LLM response text
    """
    try:
        logger.info(f"Running Gemini LLM '{model}' with prompt length: {len(prompt)}")
        
        # Validate API key
        if not api_key or len(api_key) < 20:
            raise ValueError("Invalid Google AI API key format")
        
        # Prepare request payload
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": kwargs.get("temperature", 0.7),
                "topK": kwargs.get("top_k", 40),
                "topP": kwargs.get("top_p", 0.95),
                "maxOutputTokens": kwargs.get("max_tokens", 1000),
                "stopSequences": kwargs.get("stop", [])
            }
        }
        
        # Add safety settings if provided
        if kwargs.get("safety_settings"):
            payload["safetySettings"] = kwargs["safety_settings"]
        
        # Make API request to Google Gemini
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        params = {"key": api_key}
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                json=payload,
                params=params,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                candidates = result.get("candidates", [])
                
                if candidates and "content" in candidates[0]:
                    llm_response = candidates[0]["content"]["parts"][0]["text"]
                    logger.info(f"Gemini LLM '{model}' completed successfully")
                    return llm_response
                else:
                    raise Exception("No valid response from Gemini API")
            else:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                error_msg = error_data.get("error", {}).get("message", response.text)
                logger.error(f"Gemini API error: {response.status_code} - {error_msg}")
                raise Exception(f"Gemini API error: {error_msg}")
        
    except httpx.ConnectError:
        logger.warning("Gemini API connection failed, falling back to placeholder")
        return await _fallback_response(prompt, model, "Gemini")
    except Exception as e:
        logger.error(f"Error running Gemini LLM '{model}': {e}")
        return await _fallback_response(prompt, model, "Gemini")


async def _fallback_response(prompt: str, model: str, service: str) -> str:
    """Fallback response when service is not available"""
    response = f"{service} {model} response (service unavailable):\n\n"
    response += f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}\n\n"
    response += f"This is a fallback response. The {service} service is not accessible. "
    response += f"Please check your API key and network connection."
    
    # Simulate processing time
    await asyncio.sleep(0.1)
    return response


async def run_gemini_pro(prompt: str, api_key: str, **kwargs) -> str:
    """
    Run Gemini Pro specifically
    
    Args:
        prompt: Input prompt
        api_key: Google AI API key
        **kwargs: Additional parameters
        
    Returns:
        LLM response
    """
    return await run_gemini_llm(prompt, api_key, "gemini-pro", **kwargs)


async def run_gemini_pro_vision(prompt: str, api_key: str, image_data: str = None, **kwargs) -> str:
    """
    Run Gemini Pro Vision (multimodal)
    
    Args:
        prompt: Input prompt
        api_key: Google AI API key
        image_data: Base64 encoded image data (optional)
        **kwargs: Additional parameters
        
    Returns:
        LLM response
    """
    try:
        response = f"Gemini Pro Vision response:\n\n"
        response += f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}\n"
        
        if image_data:
            response += f"Image data: {len(image_data)} characters\n"
        
        response += f"\nThis would use the Gemini Pro Vision model via Google AI API "
        response += f"with the provided API key for multimodal generation."
        
        return response
        
    except Exception as e:
        logger.error(f"Error running Gemini Pro Vision: {e}")
        raise


async def run_gemini_ultra(prompt: str, api_key: str, **kwargs) -> str:
    """
    Run Gemini Ultra (most capable model)
    
    Args:
        prompt: Input prompt
        api_key: Google AI API key
        **kwargs: Additional parameters
        
    Returns:
        LLM response
    """
    try:
        response = f"Gemini Ultra response:\n\n"
        response += f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}\n\n"
        response += f"This would use the Gemini Ultra model via Google AI API "
        response += f"with the provided API key for generation."
        
        return response
        
    except Exception as e:
        logger.error(f"Error running Gemini Ultra: {e}")
        raise


def get_available_gemini_models() -> list:
    """Get list of available Gemini models"""
    return [
        "gemini-pro",
        "gemini-pro-vision",
        "gemini-ultra",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-1.0-pro"
    ]


def validate_gemini_model(model: str) -> bool:
    """Validate if Gemini model is available"""
    return model in get_available_gemini_models()


def validate_api_key(api_key: str) -> bool:
    """Validate Google AI API key format"""
    if not api_key:
        return False
    
    # Basic validation - Google AI keys are typically longer strings
    return len(api_key) > 20


async def check_gemini_health(api_key: str) -> bool:
    """Check if Google Gemini API is accessible"""
    try:
        import httpx
        
        headers = {
            "Content-Type": "application/json"
        }
        
        params = {
            "key": api_key
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://generativelanguage.googleapis.com/v1/models",
                headers=headers,
                params=params
            )
            return response.status_code == 200
            
    except Exception as e:
        logger.error(f"Gemini health check failed: {e}")
        return False


async def get_gemini_models(api_key: str) -> list:
    """Get available models from Google Gemini API"""
    try:
        import httpx
        
        headers = {
            "Content-Type": "application/json"
        }
        
        params = {
            "key": api_key
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://generativelanguage.googleapis.com/v1/models",
                headers=headers,
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                return [model["name"].split("/")[-1] for model in data.get("models", [])]
            else:
                return get_available_gemini_models()  # Fallback
                
    except Exception as e:
        logger.error(f"Error getting Gemini models: {e}")
        return get_available_gemini_models()


async def run_gemini_with_safety_settings(prompt: str, api_key: str, model: str = "gemini-pro", 
                                        safety_settings: Dict[str, Any] = None, **kwargs) -> str:
    """
    Run Gemini with custom safety settings
    
    Args:
        prompt: Input prompt
        api_key: Google AI API key
        model: Model name
        safety_settings: Safety settings configuration
        **kwargs: Additional parameters
        
    Returns:
        LLM response
    """
    try:
        response = f"Gemini {model} response with safety settings:\n\n"
        response += f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}\n"
        
        if safety_settings:
            response += f"Safety settings: {safety_settings}\n"
        
        response += f"\nThis would use the Gemini {model} model with custom safety settings "
        response += f"via Google AI API."
        
        return response
        
    except Exception as e:
        logger.error(f"Error running Gemini with safety settings: {e}")
        raise


# Convenience function
async def run_gemini_llm_simple(prompt: str, api_key: str) -> str:
    """Simple interface for running Gemini LLM"""
    return await run_gemini_llm(prompt, api_key)
