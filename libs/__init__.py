"""
Reusable common task libraries for the Copilot Platform
"""

from .pdf_utils import PDFProcessor, extract_pdf_summary
from .web_search import WebSearcher, NewsSearcher, search_web, search_news
from .task_extraction import TaskExtractor, extract_tasks_from_text
from .dom_observer import DOMObserver, ElementTracker, FormObserver
from .utils import (
    TextUtils, DataUtils, TimeUtils, HashUtils, FileUtils,
    ValidationUtils, RetryUtils, ConfigUtils
)

__all__ = [
    'PDFProcessor', 'extract_pdf_summary',
    'WebSearcher', 'NewsSearcher', 'search_web', 'search_news',
    'TaskExtractor', 'extract_tasks_from_text',
    'DOMObserver', 'ElementTracker', 'FormObserver',
    'TextUtils', 'DataUtils', 'TimeUtils', 'HashUtils', 'FileUtils',
    'ValidationUtils', 'RetryUtils', 'ConfigUtils'
]
