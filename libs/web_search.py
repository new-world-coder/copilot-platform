"""
Web search utilities for the Copilot Platform
"""

import httpx
import asyncio
from typing import List, Dict, Any, Optional
import logging
from urllib.parse import urljoin, urlparse
import re

logger = logging.getLogger(__name__)


class WebSearcher:
    """Web search utilities"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.session = httpx.AsyncClient(timeout=30.0)
    
    async def search_google(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """Search using Google Custom Search API"""
        if not self.api_key:
            raise ValueError("Google API key required for search")
        
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": self.api_key,
                "cx": "YOUR_SEARCH_ENGINE_ID",  # Replace with actual search engine ID
                "q": query,
                "num": min(num_results, 10)
            }
            
            response = await self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get("items", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "display_url": item.get("displayLink", "")
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching Google: {e}")
            raise
    
    async def search_duckduckgo(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
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
            
            response = await self.session.get(url, params=params)
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
            for topic in data.get("RelatedTopics", [])[:num_results-1]:
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append({
                        "title": topic.get("Text", "").split(" - ")[0],
                        "url": topic.get("FirstURL", ""),
                        "snippet": topic.get("Text", ""),
                        "source": "DuckDuckGo"
                    })
            
            return results[:num_results]
            
        except Exception as e:
            logger.error(f"Error searching DuckDuckGo: {e}")
            raise
    
    async def scrape_url(self, url: str) -> Dict[str, Any]:
        """Scrape content from a URL"""
        try:
            response = await self.session.get(url)
            response.raise_for_status()
            
            html = response.text
            
            # Extract title
            title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
            title = title_match.group(1).strip() if title_match else ""
            
            # Extract meta description
            desc_match = re.search(r'<meta name="description" content="(.*?)"', html, re.IGNORECASE)
            description = desc_match.group(1).strip() if desc_match else ""
            
            # Extract text content (basic)
            text = re.sub(r'<[^>]+>', '', html)
            text = re.sub(r'\s+', ' ', text).strip()
            
            return {
                "url": url,
                "title": title,
                "description": description,
                "text": text[:2000],  # Limit text length
                "status_code": response.status_code
            }
            
        except Exception as e:
            logger.error(f"Error scraping URL {url}: {e}")
            raise
    
    async def search_and_scrape(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """Search and scrape top results"""
        try:
            # Get search results
            search_results = await self.search_duckduckgo(query, num_results)
            
            # Scrape each result
            scraped_results = []
            for result in search_results:
                if result.get("url"):
                    try:
                        scraped = await self.scrape_url(result["url"])
                        scraped_results.append({
                            **result,
                            **scraped
                        })
                    except Exception as e:
                        logger.warning(f"Failed to scrape {result['url']}: {e}")
                        scraped_results.append(result)
            
            return scraped_results
            
        except Exception as e:
            logger.error(f"Error in search and scrape: {e}")
            raise
    
    async def close(self):
        """Close the HTTP session"""
        await self.session.aclose()


class NewsSearcher(WebSearcher):
    """Specialized news search"""
    
    async def search_news(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """Search for news articles"""
        try:
            # Use DuckDuckGo news search
            url = "https://duckduckgo.com/news.js"
            params = {
                "q": query,
                "l": "us-en",
                "s": "0",
                "o": "json"
            }
            
            response = await self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("excerpt", ""),
                    "source": item.get("source", ""),
                    "date": item.get("date", ""),
                    "image": item.get("image", "")
                })
            
            return results[:num_results]
            
        except Exception as e:
            logger.error(f"Error searching news: {e}")
            raise


# Convenience functions
async def search_web(query: str, num_results: int = 10) -> List[Dict[str, Any]]:
    """Simple web search function"""
    searcher = WebSearcher()
    try:
        return await searcher.search_duckduckgo(query, num_results)
    finally:
        await searcher.close()


async def search_news(query: str, num_results: int = 10) -> List[Dict[str, Any]]:
    """Simple news search function"""
    searcher = NewsSearcher()
    try:
        return await searcher.search_news(query, num_results)
    finally:
        await searcher.close()
