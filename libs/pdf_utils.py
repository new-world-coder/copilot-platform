"""
PDF processing utilities for the Copilot Platform
"""

import fitz  # PyMuPDF
import io
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class PDFProcessor:
    """PDF processing utilities"""
    
    def __init__(self):
        self.supported_formats = ['.pdf']
    
    def extract_text(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                text += page.get_text()
            
            doc.close()
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise
    
    def extract_text_from_bytes(self, pdf_bytes: bytes) -> str:
        """Extract text from PDF bytes"""
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            text = ""
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                text += page.get_text()
            
            doc.close()
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF bytes: {e}")
            raise
    
    def extract_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """Extract metadata from PDF"""
        try:
            doc = fitz.open(pdf_path)
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
            raise
    
    def extract_images(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract images from PDF"""
        try:
            doc = fitz.open(pdf_path)
            images = []
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    
                    if pix.n - pix.alpha < 4:  # GRAY or RGB
                        img_data = pix.tobytes("png")
                        images.append({
                            "page": page_num + 1,
                            "index": img_index,
                            "data": img_data,
                            "format": "png"
                        })
                    
                    pix = None
            
            doc.close()
            return images
            
        except Exception as e:
            logger.error(f"Error extracting images from PDF: {e}")
            raise
    
    def search_text(self, pdf_path: str, search_term: str) -> List[Dict[str, Any]]:
        """Search for text in PDF"""
        try:
            doc = fitz.open(pdf_path)
            results = []
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                text_instances = page.search_for(search_term)
                
                for instance in text_instances:
                    results.append({
                        "page": page_num + 1,
                        "rect": instance,
                        "text": page.get_textbox(instance)
                    })
            
            doc.close()
            return results
            
        except Exception as e:
            logger.error(f"Error searching PDF: {e}")
            raise
    
    def get_page_text(self, pdf_path: str, page_num: int) -> str:
        """Get text from specific page"""
        try:
            doc = fitz.open(pdf_path)
            
            if page_num < 1 or page_num > doc.page_count:
                raise ValueError(f"Page number {page_num} out of range")
            
            page = doc[page_num - 1]
            text = page.get_text()
            
            doc.close()
            return text
            
        except Exception as e:
            logger.error(f"Error getting page text: {e}")
            raise


def extract_pdf_summary(pdf_path: str) -> Dict[str, Any]:
    """Extract a summary of PDF content"""
    processor = PDFProcessor()
    
    try:
        metadata = processor.extract_metadata(pdf_path)
        text = processor.extract_text(pdf_path)
        
        return {
            "metadata": metadata,
            "text_length": len(text),
            "word_count": len(text.split()),
            "has_images": len(processor.extract_images(pdf_path)) > 0,
            "preview": text[:500] + "..." if len(text) > 500 else text
        }
        
    except Exception as e:
        logger.error(f"Error creating PDF summary: {e}")
        raise
