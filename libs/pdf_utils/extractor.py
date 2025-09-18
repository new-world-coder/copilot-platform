"""
PDF Text Extraction Utilities
"""

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    fitz = None

import httpx
import asyncio
from typing import Union, Optional
import logging
from pathlib import Path
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


async def extract_text_from_pdf(url_or_path: Union[str, Path]) -> str:
    """
    Extract raw text from PDF file (URL or local path)
    
    Args:
        url_or_path: URL or local file path to PDF
        
    Returns:
        Raw text content from PDF
        
    Raises:
        ValueError: If file is not a PDF or cannot be accessed
        Exception: If extraction fails
    """
    if not PYMUPDF_AVAILABLE:
        logger.warning("PyMuPDF not available, returning placeholder text")
        return f"[PDF text extraction not available - PyMuPDF not installed. File: {url_or_path}]"
    
    try:
        # Determine if it's a URL or local path
        if is_url(url_or_path):
            pdf_content = await download_pdf(url_or_path)
        else:
            pdf_content = read_local_pdf(url_or_path)
        
        if not pdf_content:
            raise ValueError(f"Could not access PDF: {url_or_path}")
        
        # Extract text using PyMuPDF
        text = extract_text_from_bytes(pdf_content)
        
        if not text.strip():
            logger.warning(f"No text extracted from PDF: {url_or_path}")
            return ""
        
        logger.info(f"Extracted {len(text)} characters from PDF: {url_or_path}")
        return text
        
    except Exception as e:
        logger.error(f"Error extracting text from PDF {url_or_path}: {e}")
        raise


def is_url(path: Union[str, Path]) -> bool:
    """Check if path is a URL"""
    try:
        result = urlparse(str(path))
        return bool(result.scheme and result.netloc)
    except Exception:
        return False


async def download_pdf(url: str) -> Optional[bytes]:
    """Download PDF from URL"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' not in content_type and not url.lower().endswith('.pdf'):
                logger.warning(f"URL may not be a PDF: {url}")
            
            return response.content
            
    except Exception as e:
        logger.error(f"Error downloading PDF from {url}: {e}")
        return None


def read_local_pdf(path: Union[str, Path]) -> Optional[bytes]:
    """Read PDF from local file system"""
    try:
        file_path = Path(path)
        
        if not file_path.exists():
            logger.error(f"PDF file not found: {path}")
            return None
        
        if not file_path.suffix.lower() == '.pdf':
            logger.warning(f"File may not be a PDF: {path}")
        
        return file_path.read_bytes()
        
    except Exception as e:
        logger.error(f"Error reading local PDF {path}: {e}")
        return None


def extract_text_from_bytes(pdf_content: bytes) -> str:
    """Extract text from PDF bytes using PyMuPDF"""
    if not PYMUPDF_AVAILABLE:
        return "[PDF text extraction not available - PyMuPDF not installed]"
    
    try:
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        text = ""
        
        for page_num in range(doc.page_count):
            page = doc[page_num]
            page_text = page.get_text()
            text += page_text + "\n"
        
        doc.close()
        return text.strip()
        
    except Exception as e:
        logger.error(f"Error extracting text from PDF bytes: {e}")
        raise


# Convenience functions for different use cases
async def extract_text_from_url(url: str) -> str:
    """Extract text from PDF URL"""
    return await extract_text_from_pdf(url)


def extract_text_from_file(file_path: Union[str, Path]) -> str:
    """Extract text from local PDF file"""
    return asyncio.run(extract_text_from_pdf(file_path))


def extract_text_by_page(pdf_content: bytes, page_num: int) -> str:
    """Extract text from specific page"""
    try:
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        
        if page_num < 1 or page_num > doc.page_count:
            raise ValueError(f"Page number {page_num} out of range (1-{doc.page_count})")
        
        page = doc[page_num - 1]  # Convert to 0-based index
        text = page.get_text()
        
        doc.close()
        return text.strip()
        
    except Exception as e:
        logger.error(f"Error extracting text from page {page_num}: {e}")
        raise


def get_pdf_page_count(pdf_content: bytes) -> int:
    """Get total page count from PDF"""
    try:
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        page_count = doc.page_count
        doc.close()
        return page_count
        
    except Exception as e:
        logger.error(f"Error getting PDF page count: {e}")
        return 0


def extract_pdf_metadata(pdf_content: bytes) -> dict:
    """Extract metadata from PDF"""
    try:
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        metadata = doc.metadata
        
        result = {
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "subject": metadata.get("subject", ""),
            "creator": metadata.get("creator", ""),
            "producer": metadata.get("producer", ""),
            "creation_date": metadata.get("creationDate", ""),
            "modification_date": metadata.get("modDate", ""),
            "page_count": doc.page_count
        }
        
        doc.close()
        return result
        
    except Exception as e:
        logger.error(f"Error extracting PDF metadata: {e}")
        return {}
