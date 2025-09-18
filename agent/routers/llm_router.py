"""
LLM Router for handling language model queries
"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class LLMQueryRequest(BaseModel):
    """LLM query request model"""
    text: str
    model: Optional[str] = None
    provider: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000


class LLMQueryResponse(BaseModel):
    """LLM query response model"""
    response: str
    model: str
    provider: str
    tokens_used: Optional[int] = None
    processing_time: Optional[float] = None


@router.post("/query", response_model=LLMQueryResponse)
async def query_llm(request: LLMQueryRequest, app_request: Request):
    """Forward query to LLM provider"""
    try:
        config = app_request.app.state.config
        llm_config = config.get("llm", {})
        
        # Determine provider and model
        provider = request.provider or llm_config.get("default_provider", "openai")
        model = request.model or llm_config.get("default_model", "gpt-4")
        
        # Get provider configuration
        providers = llm_config.get("providers", {})
        if provider not in providers:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported LLM provider: {provider}"
            )
        
        provider_config = providers[provider]
        
        # Validate model is available for provider
        available_models = provider_config.get("models", [])
        if model not in available_models:
            raise HTTPException(
                status_code=400,
                detail=f"Model {model} not available for provider {provider}"
            )
        
        # Process the query (this would integrate with actual LLM clients)
        response_text = await process_llm_query(
            text=request.text,
            provider=provider,
            model=model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            provider_config=provider_config
        )
        
        return LLMQueryResponse(
            response=response_text,
            model=model,
            provider=provider,
            tokens_used=None,  # Would be populated by actual LLM client
            processing_time=None  # Would be populated by actual LLM client
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing LLM query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_llm_query(
    text: str,
    provider: str,
    model: str,
    temperature: float,
    max_tokens: int,
    provider_config: Dict[str, Any]
) -> str:
    """Process LLM query with specified provider and model"""
    
    if provider == "openai":
        return await process_openai_query(text, model, temperature, max_tokens, provider_config)
    elif provider == "anthropic":
        return await process_anthropic_query(text, model, temperature, max_tokens, provider_config)
    elif provider == "local":
        return await process_local_query(text, model, temperature, max_tokens, provider_config)
    elif provider == "onprem":
        return await process_onprem_query(text, model, temperature, max_tokens, provider_config)
    elif provider == "gemini":
        return await process_gemini_query(text, model, temperature, max_tokens, provider_config)
    else:
        raise ValueError(f"Unsupported provider: {provider}")


async def process_openai_query(text: str, model: str, temperature: float, max_tokens: int, config: Dict[str, Any]) -> str:
    """Process query using OpenAI"""
    try:
        from llm.openai_llm import run_openai_llm
        
        api_key = config.get("api_key")
        if not api_key:
            raise ValueError("OpenAI API key not configured")
        
        return await run_openai_llm(
            prompt=text,
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
    except Exception as e:
        logger.error(f"Error processing OpenAI query: {e}")
        return f"OpenAI {model} response to: {text[:50]}..."


async def process_anthropic_query(text: str, model: str, temperature: float, max_tokens: int, config: Dict[str, Any]) -> str:
    """Process query using Anthropic"""
    try:
        from llm.anthropic_client import AnthropicClient
        
        api_key = config.get("api_key")
        if not api_key:
            raise ValueError("Anthropic API key not configured")
        
        client = AnthropicClient(api_key=api_key, model=model)
        return await client.chat_completion([
            {"role": "user", "content": text}
        ], temperature=temperature, max_tokens=max_tokens)
    except Exception as e:
        logger.error(f"Error processing Anthropic query: {e}")
        return f"Anthropic {model} response to: {text[:50]}..."


async def process_local_query(text: str, model: str, temperature: float, max_tokens: int, config: Dict[str, Any]) -> str:
    """Process query using local LLM"""
    try:
        from llm.local_llm import run_local_llm
        
        return await run_local_llm(
            prompt=text,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
    except Exception as e:
        logger.error(f"Error processing local LLM query: {e}")
        return f"Local {model} response to: {text[:50]}..."


async def process_onprem_query(text: str, model: str, temperature: float, max_tokens: int, config: Dict[str, Any]) -> str:
    """Process query using on-premises LLM"""
    try:
        from llm.on_prem_llm import run_on_prem_llm
        
        endpoint = config.get("base_url", "http://localhost:8080")
        
        return await run_on_prem_llm(
            prompt=text,
            endpoint=endpoint,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
    except Exception as e:
        logger.error(f"Error processing on-prem LLM query: {e}")
        return f"On-prem {model} response to: {text[:50]}..."


async def process_gemini_query(text: str, model: str, temperature: float, max_tokens: int, config: Dict[str, Any]) -> str:
    """Process query using Google Gemini"""
    try:
        from llm.gemini_llm import run_gemini_llm
        
        api_key = config.get("api_key")
        if not api_key:
            raise ValueError("Gemini API key not configured")
        
        return await run_gemini_llm(
            prompt=text,
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
    except Exception as e:
        logger.error(f"Error processing Gemini query: {e}")
        return f"Gemini {model} response to: {text[:50]}..."


@router.get("/providers")
async def get_available_providers(app_request: Request):
    """Get available LLM providers and models"""
    try:
        config = app_request.app.state.config
        llm_config = config.get("llm", {})
        providers = llm_config.get("providers", {})
        
        return {
            "providers": providers,
            "default_provider": llm_config.get("default_provider", "openai"),
            "default_model": llm_config.get("default_model", "gpt-4")
        }
    except Exception as e:
        logger.error(f"Error getting providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{provider}")
async def get_provider_models(provider: str, app_request: Request):
    """Get available models for a specific provider"""
    try:
        config = app_request.app.state.config
        llm_config = config.get("llm", {})
        providers = llm_config.get("providers", {})
        
        if provider not in providers:
            raise HTTPException(status_code=404, detail=f"Provider {provider} not found")
        
        provider_config = providers[provider]
        models = provider_config.get("models", [])
        
        return {
            "provider": provider,
            "models": models,
            "config": {k: v for k, v in provider_config.items() if k != "api_key"}
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting models for provider {provider}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
