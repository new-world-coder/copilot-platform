"""
Web Search Utilities Package
"""

from .search_api import (
    search_web,
    search_bing,
    search_google,
    search_duckduckgo,
    search_news,
    search_images,
    get_available_providers,
    validate_provider,
    quick_search,
    multi_provider_search
)

__all__ = [
    'search_web',
    'search_bing',
    'search_google',
    'search_duckduckgo',
    'search_news',
    'search_images',
    'get_available_providers',
    'validate_provider',
    'quick_search',
    'multi_provider_search'
]
