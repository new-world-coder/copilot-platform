"""
Search Router for handling web search requests
"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
import httpx
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()


class SearchRequest(BaseModel):
    """Search request model"""
    query: str
    provider: Optional[str] = None
    max_results: Optional[int] = None
    search_type: Optional[str] = "web"  # web, news, images, videos


class SearchResult(BaseModel):
    """Search result model"""
    title: str
    url: str
    snippet: str
    display_url: Optional[str] = None
    source: Optional[str] = None
    date: Optional[str] = None
    image: Optional[str] = None


class SearchResponse(BaseModel):
    """Search response model"""
    success: bool
    results: List[SearchResult]
    provider: str
    query: str
    total_results: int
    processing_time: Optional[float] = None
    error: Optional[str] = None


@router.post("/", response_model=SearchResponse)
async def search(request: SearchRequest, app_request: Request):
    """Perform web search"""
    try:
        config = app_request.app.state.config
        search_config = config.get("search", {})
        
        # Determine provider
        provider = request.provider or search_config.get("default_provider", "duckduckgo")
        
        # Determine max results
        max_results = request.max_results or search_config.get("max_results", 10)
        
        # Perform search
        result = await perform_search(
            query=request.query,
            provider=provider,
            max_results=max_results,
            search_type=request.search_type,
            search_config=search_config
        )
        
        return SearchResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def perform_search(
    query: str,
    provider: str,
    max_results: int,
    search_type: str,
    search_config: Dict[str, Any]
) -> Dict[str, Any]:
    """Perform search with specified provider"""
    import time
    start_time = time.time()
    
    try:
        providers = search_config.get("providers", {})
        
        if provider == "google":
            results = await search_google(query, max_results, providers.get("google", {}))
        elif provider == "duckduckgo":
            results = await search_duckduckgo(query, max_results)
        elif provider == "bing":
            results = await search_bing(query, max_results, providers.get("bing", {}))
        else:
            raise ValueError(f"Unsupported search provider: {provider}")
        
        return {
            "success": True,
            "results": results,
            "provider": provider,
            "query": query,
            "total_results": len(results),
            "processing_time": time.time() - start_time
        }
        
    except Exception as e:
        return {
            "success": False,
            "results": [],
            "provider": provider,
            "query": query,
            "total_results": 0,
            "processing_time": time.time() - start_time,
            "error": str(e)
        }


async def search_google(query: str, max_results: int, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search using Google Custom Search API"""
    try:
        api_key = config.get("api_key")
        search_engine_id = config.get("search_engine_id")
        
        if not api_key or not search_engine_id:
            raise ValueError("Google API key and search engine ID required")
        
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": api_key,
            "cx": search_engine_id,
            "q": query,
            "num": min(max_results, 10)
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        
        results = []
        for item in data.get("items", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "display_url": item.get("displayLink", ""),
                "source": "Google"
            })
        
        return results
        
    except Exception as e:
        logger.error(f"Error searching Google: {e}")
        return []


async def search_duckduckgo(query: str, max_results: int) -> List[Dict[str, Any]]:
    """Search using DuckDuckGo (no API key required)"""
    try:
        # Use DuckDuckGo instant answer API
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        
        results = []
        
        # Extract abstract and related topics
        if data.get("Abstract"):
            results.append({
                "title": data.get("Heading", query),
                "url": data.get("AbstractURL", ""),
                "snippet": data.get("Abstract", ""),
                "source": "DuckDuckGo"
            })
        
        # Add related topics
        for topic in data.get("RelatedTopics", [])[:max_results-1]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append({
                    "title": topic.get("Text", "").split(" - ")[0],
                    "url": topic.get("FirstURL", ""),
                    "snippet": topic.get("Text", ""),
                    "source": "DuckDuckGo"
                })
        
        return results[:max_results]
        
    except Exception as e:
        logger.error(f"Error searching DuckDuckGo: {e}")
        return []


async def search_bing(query: str, max_results: int, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search using Bing Search API"""
    try:
        api_key = config.get("api_key")
        
        if not api_key:
            raise ValueError("Bing API key required")
        
        url = "https://api.bing.microsoft.com/v7.0/search"
        headers = {
            "Ocp-Apim-Subscription-Key": api_key
        }
        params = {
            "q": query,
            "count": min(max_results, 50)
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
        
        results = []
        for item in data.get("webPages", {}).get("value", []):
            results.append({
                "title": item.get("name", ""),
                "url": item.get("url", ""),
                "snippet": item.get("snippet", ""),
                "display_url": item.get("displayUrl", ""),
                "source": "Bing"
            })
        
        return results
        
    except Exception as e:
        logger.error(f"Error searching Bing: {e}")
        return []


@router.get("/providers")
async def get_search_providers(app_request: Request):
    """Get available search providers"""
    try:
        config = app_request.app.state.config
        search_config = config.get("search", {})
        providers = search_config.get("providers", {})
        
        return {
            "providers": list(providers.keys()),
            "default_provider": search_config.get("default_provider", "duckduckgo"),
            "max_results": search_config.get("max_results", 10)
        }
    except Exception as e:
        logger.error(f"Error getting search providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/news")
async def search_news(query: str, max_results: int = 10, app_request: Request = None):
    """Search for news articles"""
    try:
        # This would implement news-specific search
        # For now, use regular search with news context
        request = SearchRequest(
            query=f"news {query}",
            max_results=max_results,
            search_type="news"
        )
        
        return await search(request, app_request)
        
    except Exception as e:
        logger.error(f"Error searching news: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/images")
async def search_images(query: str, max_results: int = 10, app_request: Request = None):
    """Search for images"""
    try:
        # This would implement image-specific search
        # For now, return placeholder
        return {
            "success": True,
            "results": [],
            "provider": "placeholder",
            "query": query,
            "total_results": 0,
            "message": "Image search not yet implemented"
        }
        
    except Exception as e:
        logger.error(f"Error searching images: {e}")
        raise HTTPException(status_code=500, detail=str(e))
