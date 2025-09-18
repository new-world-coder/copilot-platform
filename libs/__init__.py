"""
Reusable common task libraries for the Copilot Platform
"""

# Import only what actually exists
try:
    from .pdf_utils import extract_text_from_pdf, highlight_terms
    PDF_UTILS_AVAILABLE = True
except ImportError:
    PDF_UTILS_AVAILABLE = False

try:
    from .web_search import search_web
    WEB_SEARCH_AVAILABLE = True
except ImportError:
    WEB_SEARCH_AVAILABLE = False

try:
    from .task_extraction.llm_task_parser import TaskExtractor
    TASK_EXTRACTION_AVAILABLE = True
except ImportError:
    TASK_EXTRACTION_AVAILABLE = False

__all__ = [
    'extract_text_from_pdf',
    'highlight_terms', 
    'search_web',
    'TaskExtractor'
]
