"""
PDF Utilities Package
"""

from .extractor import (
    extract_text_from_pdf,
    extract_text_from_url,
    extract_text_from_file,
    extract_text_by_page,
    get_pdf_page_count,
    extract_pdf_metadata
)

from .highlighter import (
    highlight_terms,
    highlight_legal_terms,
    highlight_dates,
    highlight_amounts,
    highlight_names,
    combine_highlights,
    format_highlighted_text,
    highlight_all
)

__all__ = [
    # Extractor functions
    'extract_text_from_pdf',
    'extract_text_from_url', 
    'extract_text_from_file',
    'extract_text_by_page',
    'get_pdf_page_count',
    'extract_pdf_metadata',
    
    # Highlighter functions
    'highlight_terms',
    'highlight_legal_terms',
    'highlight_dates',
    'highlight_amounts', 
    'highlight_names',
    'combine_highlights',
    'format_highlighted_text',
    'highlight_all'
]
