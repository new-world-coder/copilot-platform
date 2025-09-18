"""
PDF Text Highlighting Utilities
"""

import re
from typing import List, Dict, Any, Union
import logging

logger = logging.getLogger(__name__)


def highlight_terms(text: str, terms: List[str]) -> List[Dict[str, Any]]:
    """
    Highlight terms in text and return annotated spans
    
    Args:
        text: Input text to search
        terms: List of terms to highlight
        
    Returns:
        List of annotated spans with start, end, text, and term information
    """
    try:
        if not text or not terms:
            return []
        
        annotated_spans = []
        text_lower = text.lower()
        
        for term in terms:
            if not term.strip():
                continue
                
            # Find all occurrences of the term (case-insensitive)
            spans = find_term_spans(text, text_lower, term.strip())
            
            for span in spans:
                annotated_spans.append({
                    "start": span["start"],
                    "end": span["end"],
                    "text": span["text"],
                    "term": term,
                    "type": "highlight",
                    "confidence": span.get("confidence", 1.0)
                })
        
        # Sort spans by start position
        annotated_spans.sort(key=lambda x: x["start"])
        
        # Remove overlapping spans (keep the first one)
        annotated_spans = remove_overlapping_spans(annotated_spans)
        
        logger.info(f"Found {len(annotated_spans)} highlighted spans for {len(terms)} terms")
        return annotated_spans
        
    except Exception as e:
        logger.error(f"Error highlighting terms: {e}")
        return []


def find_term_spans(text: str, text_lower: str, term: str) -> List[Dict[str, Any]]:
    """Find all spans of a term in text"""
    spans = []
    term_lower = term.lower()
    
    # Use regex to find word boundaries for better matching
    pattern = re.escape(term_lower)
    
    for match in re.finditer(pattern, text_lower):
        start = match.start()
        end = match.end()
        
        # Extract the actual text (preserving original case)
        matched_text = text[start:end]
        
        spans.append({
            "start": start,
            "end": end,
            "text": matched_text,
            "confidence": calculate_confidence(matched_text, term)
        })
    
    return spans


def calculate_confidence(matched_text: str, original_term: str) -> float:
    """Calculate confidence score for a match"""
    # Exact case match gets higher confidence
    if matched_text == original_term:
        return 1.0
    
    # Case-insensitive match gets medium confidence
    if matched_text.lower() == original_term.lower():
        return 0.8
    
    # Partial match gets lower confidence
    return 0.6


def remove_overlapping_spans(spans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove overlapping spans, keeping the first occurrence"""
    if not spans:
        return []
    
    # Sort by start position
    sorted_spans = sorted(spans, key=lambda x: x["start"])
    filtered_spans = [sorted_spans[0]]
    
    for span in sorted_spans[1:]:
        last_span = filtered_spans[-1]
        
        # Check if spans overlap
        if span["start"] >= last_span["end"]:
            filtered_spans.append(span)
        else:
            # Spans overlap, keep the one with higher confidence
            if span["confidence"] > last_span["confidence"]:
                filtered_spans[-1] = span
    
    return filtered_spans


def highlight_legal_terms(text: str) -> List[Dict[str, Any]]:
    """Highlight common legal terms"""
    legal_terms = [
        "agreement", "contract", "party", "parties", "whereas", "therefore",
        "liability", "indemnification", "confidentiality", "termination",
        "breach", "remedy", "damages", "jurisdiction", "governing law",
        "force majeure", "assignment", "amendment", "waiver", "severability"
    ]
    
    return highlight_terms(text, legal_terms)


def highlight_dates(text: str) -> List[Dict[str, Any]]:
    """Highlight date patterns in text"""
    date_patterns = [
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY or DD/MM/YYYY
        r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',    # YYYY/MM/DD
        r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}\b',  # Month DD, YYYY
        r'\b\d{1,2}\s+(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4}\b',  # DD Month YYYY
        r'\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',  # Day names
        r'\b(?:today|tomorrow|yesterday)\b'  # Relative dates
    ]
    
    spans = []
    for pattern in date_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            spans.append({
                "start": match.start(),
                "end": match.end(),
                "text": match.group(),
                "term": "date",
                "type": "date",
                "confidence": 1.0
            })
    
    return spans


def highlight_amounts(text: str) -> List[Dict[str, Any]]:
    """Highlight monetary amounts and numbers"""
    amount_patterns = [
        r'\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?',  # $1,234.56
        r'\b\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars?|USD)\b',  # 1,234.56 dollars
        r'\b\d+(?:\.\d+)?\s*(?:percent|%)\b',  # 25% or 25 percent
        r'\b\d+(?:\.\d+)?\s*(?:million|billion|thousand)\b'  # 1.5 million
    ]
    
    spans = []
    for pattern in amount_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            spans.append({
                "start": match.start(),
                "end": match.end(),
                "text": match.group(),
                "term": "amount",
                "type": "amount",
                "confidence": 1.0
            })
    
    return spans


def highlight_names(text: str) -> List[Dict[str, Any]]:
    """Highlight potential names (simple heuristic)"""
    # Look for capitalized words that might be names
    name_pattern = r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'
    
    spans = []
    for match in re.finditer(name_pattern, text):
        spans.append({
            "start": match.start(),
            "end": match.end(),
            "text": match.group(),
            "term": "name",
            "type": "name",
            "confidence": 0.7  # Lower confidence for heuristic matching
        })
    
    return spans


def combine_highlights(*highlight_lists: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Combine multiple highlight lists and remove overlaps"""
    all_spans = []
    for highlight_list in highlight_lists:
        all_spans.extend(highlight_list)
    
    # Sort by start position
    all_spans.sort(key=lambda x: x["start"])
    
    # Remove overlaps
    return remove_overlapping_spans(all_spans)


def format_highlighted_text(text: str, spans: List[Dict[str, Any]], 
                          highlight_format: str = "**{text}**") -> str:
    """Format text with highlighted spans"""
    if not spans:
        return text
    
    # Sort spans by start position (descending) to avoid index issues
    sorted_spans = sorted(spans, key=lambda x: x["start"], reverse=True)
    
    formatted_text = text
    for span in sorted_spans:
        start = span["start"]
        end = span["end"]
        highlighted_text = highlight_format.format(text=span["text"])
        formatted_text = formatted_text[:start] + highlighted_text + formatted_text[end:]
    
    return formatted_text


# Convenience function for common highlighting tasks
def highlight_all(text: str, terms: List[str] = None) -> List[Dict[str, Any]]:
    """Highlight terms, dates, amounts, and names in text"""
    all_highlights = []
    
    # Highlight custom terms
    if terms:
        all_highlights.extend(highlight_terms(text, terms))
    
    # Highlight common patterns
    all_highlights.extend(highlight_dates(text))
    all_highlights.extend(highlight_amounts(text))
    all_highlights.extend(highlight_names(text))
    
    # Combine and remove overlaps
    return combine_highlights(*all_highlights)
