"""
Task Extraction Rules for Legal Documents
Regex-based extraction for deadlines, dates, and legal terms
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class LegalTaskExtractor:
    """Extract tasks, deadlines, and dates from legal documents"""
    
    def __init__(self):
        self.deadline_patterns = self._compile_deadline_patterns()
        self.date_patterns = self._compile_date_patterns()
        self.legal_action_patterns = self._compile_legal_action_patterns()
        self.party_patterns = self._compile_party_patterns()
    
    def _compile_deadline_patterns(self) -> List[Tuple[str, str]]:
        """Compile regex patterns for deadline extraction"""
        return [
            # Specific deadline phrases
            (r'(?:deadline|due date|due by|must be completed by|expires on|expires at)\s*:?\s*([^.!?\n]+)', 'deadline'),
            (r'(?:no later than|not later than|by no later than)\s+([^.!?\n]+)', 'deadline'),
            (r'(?:within|in)\s+(\d+)\s+(?:days?|weeks?|months?|years?)\s+(?:of|from)', 'relative_deadline'),
            (r'(?:within|in)\s+(\d+)\s+(?:business\s+)?days?\s+(?:of|from)', 'business_deadline'),
            
            # Contract-specific deadlines
            (r'(?:termination|expiration)\s+(?:date|period)\s*:?\s*([^.!?\n]+)', 'contract_deadline'),
            (r'(?:renewal|extension)\s+(?:date|period)\s*:?\s*([^.!?\n]+)', 'renewal_deadline'),
            (r'(?:notice\s+period|notification\s+period)\s*:?\s*([^.!?\n]+)', 'notice_deadline'),
            
            # Payment deadlines
            (r'(?:payment\s+due|payment\s+date|invoice\s+due)\s*:?\s*([^.!?\n]+)', 'payment_deadline'),
            (r'(?:net\s+\d+|n\/\d+)\s+(?:days?|days\s+from\s+invoice)', 'payment_terms'),
        ]
    
    def _compile_date_patterns(self) -> List[Tuple[str, str]]:
        """Compile regex patterns for date extraction"""
        return [
            # Standard date formats
            (r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b', 'mm_dd_yyyy'),
            (r'\b(\d{4}[/-]\d{1,2}[/-]\d{1,2})\b', 'yyyy_mm_dd'),
            (r'\b(\d{1,2}\s+(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4})\b', 'dd_month_yyyy'),
            (r'\b((?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4})\b', 'month_dd_yyyy'),
            
            # Relative dates
            (r'\b(today|tomorrow|yesterday)\b', 'relative_date'),
            (r'\b(this|next|last)\s+(?:week|month|year|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', 'relative_period'),
            
            # Time periods
            (r'\b(\d+)\s+(?:days?|weeks?|months?|years?)\s+(?:ago|from\s+now|hence)\b', 'relative_time'),
        ]
    
    def _compile_legal_action_patterns(self) -> List[Tuple[str, str]]:
        """Compile regex patterns for legal actions"""
        return [
            # Obligations and requirements
            (r'(?:shall|must|will|agrees to|undertakes to|is required to)\s+([^.!?\n]+)', 'obligation'),
            (r'(?:obligation|duty|responsibility)\s*:?\s*([^.!?\n]+)', 'obligation'),
            
            # Rights and permissions
            (r'(?:right|entitlement|privilege)\s*:?\s*([^.!?\n]+)', 'right'),
            (r'(?:may|can|could|is entitled to|has the right to)\s+([^.!?\n]+)', 'permission'),
            
            # Prohibitions
            (r'(?:shall not|must not|will not|cannot|may not|prohibited from)\s+([^.!?\n]+)', 'prohibition'),
            (r'(?:prohibition|restriction|limitation)\s*:?\s*([^.!?\n]+)', 'prohibition'),
            
            # Legal actions
            (r'(?:file|submit|provide|deliver|furnish|present)\s+([^.!?\n]+)', 'action'),
            (r'(?:notify|inform|advise|alert)\s+([^.!?\n]+)', 'notification'),
            (r'(?:review|examine|inspect|audit)\s+([^.!?\n]+)', 'review'),
            (r'(?:approve|authorize|consent to|agree to)\s+([^.!?\n]+)', 'approval'),
        ]
    
    def _compile_party_patterns(self) -> List[Tuple[str, str]]:
        """Compile regex patterns for party identification"""
        return [
            (r'(?:party|parties)\s*:?\s*([A-Z][A-Za-z\s&,\.]+)', 'party'),
            (r'(?:plaintiff|defendant|appellant|appellee|petitioner|respondent)\s*:?\s*([A-Z][A-Za-z\s&,\.]+)', 'legal_party'),
            (r'([A-Z][A-Za-z\s&,\.]+)\s+(?:company|corporation|llc|inc\.?|ltd\.?)', 'entity'),
            (r'between\s+([A-Z][A-Za-z\s&,\.]+)\s+and\s+([A-Z][A-Za-z\s&,\.]+)', 'parties_between'),
        ]
    
    def extract_deadlines(self, text: str) -> List[Dict[str, Any]]:
        """Extract deadlines from legal document text"""
        deadlines = []
        
        for pattern, pattern_type in self.deadline_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                deadline_text = match.group(1).strip() if match.groups() else match.group(0).strip()
                
                # Extract dates from deadline text
                dates = self._extract_dates_from_text(deadline_text)
                
                deadlines.append({
                    "type": "deadline",
                    "pattern_type": pattern_type,
                    "text": deadline_text,
                    "full_match": match.group(0),
                    "dates": dates,
                    "start_pos": match.start(),
                    "end_pos": match.end(),
                    "confidence": self._calculate_confidence(pattern_type, deadline_text)
                })
        
        return deadlines
    
    def extract_dates(self, text: str) -> List[Dict[str, Any]]:
        """Extract dates from legal document text"""
        dates = []
        
        for pattern, pattern_type in self.date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                date_text = match.group(1) if match.groups() else match.group(0)
                
                # Parse the date
                parsed_date = self._parse_date(date_text, pattern_type)
                
                dates.append({
                    "type": "date",
                    "pattern_type": pattern_type,
                    "text": date_text,
                    "full_match": match.group(0),
                    "parsed_date": parsed_date,
                    "start_pos": match.start(),
                    "end_pos": match.end(),
                    "confidence": self._calculate_date_confidence(pattern_type, date_text)
                })
        
        return dates
    
    def extract_legal_actions(self, text: str) -> List[Dict[str, Any]]:
        """Extract legal actions from document text"""
        actions = []
        
        for pattern, pattern_type in self.legal_action_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                action_text = match.group(1).strip() if match.groups() else match.group(0).strip()
                
                # Extract dates and deadlines from action text
                dates = self._extract_dates_from_text(action_text)
                deadlines = self._extract_deadlines_from_text(action_text)
                
                actions.append({
                    "type": "legal_action",
                    "pattern_type": pattern_type,
                    "text": action_text,
                    "full_match": match.group(0),
                    "dates": dates,
                    "deadlines": deadlines,
                    "start_pos": match.start(),
                    "end_pos": match.end(),
                    "confidence": self._calculate_confidence(pattern_type, action_text)
                })
        
        return actions
    
    def extract_parties(self, text: str) -> List[Dict[str, Any]]:
        """Extract parties from legal document text"""
        parties = []
        
        for pattern, pattern_type in self.party_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                if pattern_type == "parties_between":
                    # Special handling for "between X and Y" pattern
                    party1 = match.group(1).strip()
                    party2 = match.group(2).strip()
                    parties.extend([
                        {
                            "type": "party",
                            "pattern_type": pattern_type,
                            "text": party1,
                            "full_match": match.group(0),
                            "start_pos": match.start(),
                            "end_pos": match.end(),
                            "confidence": 0.9
                        },
                        {
                            "type": "party",
                            "pattern_type": pattern_type,
                            "text": party2,
                            "full_match": match.group(0),
                            "start_pos": match.start(),
                            "end_pos": match.end(),
                            "confidence": 0.9
                        }
                    ])
                else:
                    party_text = match.group(1).strip() if match.groups() else match.group(0).strip()
                    parties.append({
                        "type": "party",
                        "pattern_type": pattern_type,
                        "text": party_text,
                        "full_match": match.group(0),
                        "start_pos": match.start(),
                        "end_pos": match.end(),
                        "confidence": self._calculate_confidence(pattern_type, party_text)
                    })
        
        return parties
    
    def _extract_dates_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract dates from a specific text snippet"""
        dates = []
        
        for pattern, pattern_type in self.date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                date_text = match.group(1) if match.groups() else match.group(0)
                parsed_date = self._parse_date(date_text, pattern_type)
                
                dates.append({
                    "text": date_text,
                    "pattern_type": pattern_type,
                    "parsed_date": parsed_date
                })
        
        return dates
    
    def _extract_deadlines_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract deadlines from a specific text snippet"""
        deadlines = []
        
        for pattern, pattern_type in self.deadline_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                deadline_text = match.group(1).strip() if match.groups() else match.group(0).strip()
                
                deadlines.append({
                    "text": deadline_text,
                    "pattern_type": pattern_type
                })
        
        return deadlines
    
    def _parse_date(self, date_text: str, pattern_type: str) -> Optional[datetime]:
        """Parse date text into datetime object"""
        try:
            date_text = date_text.strip().lower()
            
            if pattern_type == "relative_date":
                today = datetime.now().date()
                if date_text == "today":
                    return datetime.combine(today, datetime.min.time())
                elif date_text == "tomorrow":
                    return datetime.combine(today + timedelta(days=1), datetime.min.time())
                elif date_text == "yesterday":
                    return datetime.combine(today - timedelta(days=1), datetime.min.time())
            
            elif pattern_type == "relative_period":
                # Handle "this week", "next month", etc.
                today = datetime.now()
                if "this week" in date_text:
                    return today
                elif "next week" in date_text:
                    return today + timedelta(weeks=1)
                elif "this month" in date_text:
                    return today
                elif "next month" in date_text:
                    return today + timedelta(days=30)
            
            elif pattern_type == "relative_time":
                # Handle "5 days ago", "2 weeks from now", etc.
                numbers = re.findall(r'\d+', date_text)
                if numbers:
                    num = int(numbers[0])
                    if "days" in date_text:
                        if "ago" in date_text:
                            return datetime.now() - timedelta(days=num)
                        else:
                            return datetime.now() + timedelta(days=num)
                    elif "weeks" in date_text:
                        if "ago" in date_text:
                            return datetime.now() - timedelta(weeks=num)
                        else:
                            return datetime.now() + timedelta(weeks=num)
            
            else:
                # Try to parse standard date formats
                date_formats = [
                    "%m/%d/%Y", "%m-%d-%Y", "%d/%m/%Y", "%d-%m-%Y",
                    "%Y/%m/%d", "%Y-%m-%d", "%B %d, %Y", "%d %B %Y"
                ]
                
                for fmt in date_formats:
                    try:
                        return datetime.strptime(date_text, fmt)
                    except ValueError:
                        continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing date '{date_text}': {e}")
            return None
    
    def _calculate_confidence(self, pattern_type: str, text: str) -> float:
        """Calculate confidence score for extracted item"""
        base_confidence = {
            "deadline": 0.9,
            "relative_deadline": 0.8,
            "business_deadline": 0.85,
            "contract_deadline": 0.9,
            "payment_deadline": 0.8,
            "obligation": 0.8,
            "right": 0.7,
            "permission": 0.7,
            "prohibition": 0.8,
            "action": 0.7,
            "party": 0.8,
            "legal_party": 0.9,
            "entity": 0.8
        }
        
        confidence = base_confidence.get(pattern_type, 0.5)
        
        # Adjust confidence based on text length and content
        if len(text) < 5:
            confidence *= 0.7
        elif len(text) > 100:
            confidence *= 0.8
        
        # Boost confidence for legal terms
        legal_terms = ["shall", "must", "agreement", "contract", "party", "obligation"]
        if any(term in text.lower() for term in legal_terms):
            confidence *= 1.1
        
        return min(confidence, 1.0)
    
    def _calculate_date_confidence(self, pattern_type: str, text: str) -> float:
        """Calculate confidence score for date extraction"""
        base_confidence = {
            "mm_dd_yyyy": 0.9,
            "yyyy_mm_dd": 0.9,
            "dd_month_yyyy": 0.8,
            "month_dd_yyyy": 0.8,
            "relative_date": 0.9,
            "relative_period": 0.7,
            "relative_time": 0.8
        }
        
        confidence = base_confidence.get(pattern_type, 0.5)
        
        # Adjust based on text clarity
        if len(text) < 3:
            confidence *= 0.5
        elif len(text) > 50:
            confidence *= 0.8
        
        return min(confidence, 1.0)


# Convenience functions
def extract_deadlines_from_legal_doc(text: str) -> List[Dict[str, Any]]:
    """Extract deadlines from legal document text"""
    extractor = LegalTaskExtractor()
    return extractor.extract_deadlines(text)


def extract_dates_from_legal_doc(text: str) -> List[Dict[str, Any]]:
    """Extract dates from legal document text"""
    extractor = LegalTaskExtractor()
    return extractor.extract_dates(text)


def extract_legal_actions_from_doc(text: str) -> List[Dict[str, Any]]:
    """Extract legal actions from document text"""
    extractor = LegalTaskExtractor()
    return extractor.extract_legal_actions(text)


def extract_parties_from_doc(text: str) -> List[Dict[str, Any]]:
    """Extract parties from legal document text"""
    extractor = LegalTaskExtractor()
    return extractor.extract_parties(text)


def extract_all_legal_elements(text: str) -> Dict[str, List[Dict[str, Any]]]:
    """Extract all legal elements from document text"""
    extractor = LegalTaskExtractor()
    
    return {
        "deadlines": extractor.extract_deadlines(text),
        "dates": extractor.extract_dates(text),
        "legal_actions": extractor.extract_legal_actions(text),
        "parties": extractor.extract_parties(text)
    }
