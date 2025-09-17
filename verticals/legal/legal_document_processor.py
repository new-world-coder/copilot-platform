"""
Legal document processing utilities
"""

import re
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class LegalDocumentProcessor:
    """Process various types of legal documents"""
    
    def __init__(self):
        self.document_types = {
            'contract': ['agreement', 'contract', 'terms', 'conditions'],
            'brief': ['brief', 'motion', 'petition', 'complaint'],
            'opinion': ['opinion', 'decision', 'ruling', 'judgment'],
            'statute': ['statute', 'law', 'regulation', 'code'],
            'case': ['case', 'lawsuit', 'litigation', 'proceeding']
        }
        
        self.legal_citations = [
            r'\d+\s+[A-Za-z]+\s+\d+',  # Case citations
            r'\d+\s+U\.S\.C\.\s+\d+',   # USC citations
            r'\d+\s+C\.F\.R\.\s+\d+',   # CFR citations
            r'[A-Za-z]+\s+v\.\s+[A-Za-z]+',  # Case names
        ]
    
    def process_document(self, document_text: str, doc_type: Optional[str] = None) -> Dict[str, Any]:
        """Process a legal document and extract key information"""
        try:
            if not doc_type:
                doc_type = self._identify_document_type(document_text)
            
            processor = self._get_processor(doc_type)
            return processor(document_text)
            
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            raise
    
    def _identify_document_type(self, text: str) -> str:
        """Identify the type of legal document"""
        text_lower = text.lower()
        
        scores = {}
        for doc_type, keywords in self.document_types.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            scores[doc_type] = score
        
        return max(scores, key=scores.get) if scores else 'unknown'
    
    def _get_processor(self, doc_type: str):
        """Get the appropriate processor for document type"""
        processors = {
            'contract': self._process_contract,
            'brief': self._process_brief,
            'opinion': self._process_opinion,
            'statute': self._process_statute,
            'case': self._process_case
        }
        
        return processors.get(doc_type, self._process_generic)
    
    def _process_contract(self, text: str) -> Dict[str, Any]:
        """Process contract documents"""
        return {
            'type': 'contract',
            'parties': self._extract_parties(text),
            'key_terms': self._extract_key_terms(text),
            'obligations': self._extract_obligations(text),
            'rights': self._extract_rights(text),
            'dates': self._extract_dates(text),
            'financial_terms': self._extract_financial_terms(text),
            'termination_clauses': self._extract_termination_clauses(text),
            'governing_law': self._extract_governing_law(text)
        }
    
    def _process_brief(self, text: str) -> Dict[str, Any]:
        """Process legal briefs"""
        return {
            'type': 'brief',
            'court': self._extract_court(text),
            'case_number': self._extract_case_number(text),
            'parties': self._extract_parties(text),
            'issues': self._extract_issues(text),
            'arguments': self._extract_arguments(text),
            'citations': self._extract_citations(text),
            'relief_sought': self._extract_relief_sought(text)
        }
    
    def _process_opinion(self, text: str) -> Dict[str, Any]:
        """Process court opinions"""
        return {
            'type': 'opinion',
            'court': self._extract_court(text),
            'case_name': self._extract_case_name(text),
            'case_number': self._extract_case_number(text),
            'date': self._extract_decision_date(text),
            'judge': self._extract_judge(text),
            'holding': self._extract_holding(text),
            'reasoning': self._extract_reasoning(text),
            'citations': self._extract_citations(text)
        }
    
    def _process_statute(self, text: str) -> Dict[str, Any]:
        """Process statutes and regulations"""
        return {
            'type': 'statute',
            'title': self._extract_title(text),
            'section': self._extract_section(text),
            'effective_date': self._extract_effective_date(text),
            'definitions': self._extract_definitions(text),
            'prohibitions': self._extract_prohibitions(text),
            'requirements': self._extract_requirements(text),
            'penalties': self._extract_penalties(text)
        }
    
    def _process_case(self, text: str) -> Dict[str, Any]:
        """Process case documents"""
        return {
            'type': 'case',
            'case_name': self._extract_case_name(text),
            'case_number': self._extract_case_number(text),
            'court': self._extract_court(text),
            'parties': self._extract_parties(text),
            'claims': self._extract_claims(text),
            'defenses': self._extract_defenses(text),
            'status': self._extract_case_status(text)
        }
    
    def _process_generic(self, text: str) -> Dict[str, Any]:
        """Process generic legal documents"""
        return {
            'type': 'generic',
            'title': self._extract_title(text),
            'parties': self._extract_parties(text),
            'dates': self._extract_dates(text),
            'citations': self._extract_citations(text),
            'key_terms': self._extract_key_terms(text)
        }
    
    def _extract_parties(self, text: str) -> List[str]:
        """Extract party names"""
        parties = []
        
        patterns = [
            r'(?:plaintiff|defendant|appellant|appellee|petitioner|respondent)[:\s]*([A-Z][A-Za-z\s&,\.]+)',
            r'([A-Z][A-Za-z\s&,\.]+)\s+(?:v\.|vs\.|versus)\s+([A-Z][A-Za-z\s&,\.]+)',
            r'([A-Z][A-Za-z\s&,\.]+)\s+(?:company|corporation|llc|inc\.?)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) == 2:
                    parties.extend([match.group(1).strip(), match.group(2).strip()])
                else:
                    parties.append(match.group(1).strip())
        
        return list(set(parties))  # Remove duplicates
    
    def _extract_key_terms(self, text: str) -> Dict[str, str]:
        """Extract key terms and definitions"""
        terms = {}
        
        patterns = [
            r'"([^"]+)"\s*means?\s*([^.!?\n]+)',
            r'([A-Z][A-Za-z\s]+)\s*means?\s*([^.!?\n]+)',
            r'([A-Z][A-Za-z\s]+)\s*is\s+defined\s+as\s+([^.!?\n]+)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                term = match.group(1).strip()
                definition = match.group(2).strip()
                if len(term) > 2 and len(definition) > 5:
                    terms[term] = definition
        
        return terms
    
    def _extract_obligations(self, text: str) -> List[str]:
        """Extract obligations from contract"""
        obligations = []
        
        patterns = [
            r'(?:shall|must|will|agrees to|undertakes to)\s+([^.!?\n]+)',
            r'(?:obligation|duty|responsibility)[:\s]*([^.!?\n]+)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                obligations.append(match.group(1).strip())
        
        return obligations
    
    def _extract_rights(self, text: str) -> List[str]:
        """Extract rights from contract"""
        rights = []
        
        patterns = [
            r'(?:right|entitlement|privilege)[:\s]*([^.!?\n]+)',
            r'(?:may|can|could)\s+([^.!?\n]+)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                rights.append(match.group(1).strip())
        
        return rights
    
    def _extract_dates(self, text: str) -> List[Dict[str, str]]:
        """Extract important dates"""
        dates = []
        
        patterns = [
            r'(?:date|effective|commencement|expiration|termination)[:\s]*([^.!?\n]+)',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                dates.append({
                    'date': match.group(1).strip(),
                    'context': match.group(0).strip()
                })
        
        return dates
    
    def _extract_financial_terms(self, text: str) -> Dict[str, str]:
        """Extract financial terms"""
        financial_terms = {}
        
        patterns = {
            'amount': r'(?:amount|payment|price|cost)[:\s]*\$?([0-9,]+(?:\.[0-9]{2})?)',
            'currency': r'([A-Z]{3})\s+(?:currency|dollars?)',
            'payment_terms': r'(?:payment\s+terms?)[:\s]*([^.!?\n]+)'
        }
        
        for term_type, pattern in patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                financial_terms[term_type] = match.group(1).strip()
        
        return financial_terms
    
    def _extract_termination_clauses(self, text: str) -> List[str]:
        """Extract termination clauses"""
        termination_clauses = []
        
        pattern = r'(?:termination|expiration|end)[^.!?]*?[.!?]'
        matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            termination_clauses.append(match.group(0).strip())
        
        return termination_clauses
    
    def _extract_governing_law(self, text: str) -> str:
        """Extract governing law clause"""
        pattern = r'(?:governing\s+law|jurisdiction)[:\s]*([^.!?\n]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        
        return match.group(1).strip() if match else ""
    
    def _extract_court(self, text: str) -> str:
        """Extract court information"""
        patterns = [
            r'(?:court|tribunal)[:\s]*([^.!?\n]+)',
            r'([A-Z][A-Za-z\s]+)\s+(?:court|tribunal)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _extract_case_number(self, text: str) -> str:
        """Extract case number"""
        pattern = r'(?:case\s+number|docket\s+number)[:\s]*([A-Za-z0-9-]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        
        return match.group(1).strip() if match else ""
    
    def _extract_issues(self, text: str) -> List[str]:
        """Extract legal issues"""
        issues = []
        
        patterns = [
            r'(?:issue|question)[:\s]*([^.!?\n]+)',
            r'(?:whether|if)\s+([^.!?\n]+)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                issues.append(match.group(1).strip())
        
        return issues
    
    def _extract_arguments(self, text: str) -> List[str]:
        """Extract legal arguments"""
        arguments = []
        
        pattern = r'(?:argument|contention)[:\s]*([^.!?\n]+)'
        matches = re.finditer(pattern, text, re.IGNORECASE)
        
        for match in matches:
            arguments.append(match.group(1).strip())
        
        return arguments
    
    def _extract_citations(self, text: str) -> List[str]:
        """Extract legal citations"""
        citations = []
        
        for pattern in self.legal_citations:
            matches = re.finditer(pattern, text)
            for match in matches:
                citations.append(match.group(0).strip())
        
        return citations
    
    def _extract_relief_sought(self, text: str) -> str:
        """Extract relief sought"""
        pattern = r'(?:relief|remedy|prayer)[:\s]*([^.!?\n]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        
        return match.group(1).strip() if match else ""
    
    def _extract_case_name(self, text: str) -> str:
        """Extract case name"""
        pattern = r'([A-Z][A-Za-z\s&,\.]+)\s+(?:v\.|vs\.|versus)\s+([A-Z][A-Za-z\s&,\.]+)'
        match = re.search(pattern, text)
        
        if match:
            return f"{match.group(1).strip()} v. {match.group(2).strip()}"
        
        return ""
    
    def _extract_decision_date(self, text: str) -> str:
        """Extract decision date"""
        pattern = r'(?:decided|ruled|opinion)[:\s]*([^.!?\n]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        
        return match.group(1).strip() if match else ""
    
    def _extract_judge(self, text: str) -> str:
        """Extract judge name"""
        pattern = r'(?:judge|justice)[:\s]*([A-Z][A-Za-z\s]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        
        return match.group(1).strip() if match else ""
    
    def _extract_holding(self, text: str) -> str:
        """Extract court holding"""
        pattern = r'(?:holding|decision)[:\s]*([^.!?\n]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        
        return match.group(1).strip() if match else ""
    
    def _extract_reasoning(self, text: str) -> List[str]:
        """Extract court reasoning"""
        reasoning = []
        
        pattern = r'(?:reasoning|analysis)[:\s]*([^.!?\n]+)'
        matches = re.finditer(pattern, text, re.IGNORECASE)
        
        for match in matches:
            reasoning.append(match.group(1).strip())
        
        return reasoning
    
    def _extract_title(self, text: str) -> str:
        """Extract document title"""
        # Look for title in first few lines
        lines = text.split('\n')[:5]
        for line in lines:
            line = line.strip()
            if line and len(line) > 10:
                return line
        
        return ""
    
    def _extract_section(self, text: str) -> str:
        """Extract section number"""
        pattern = r'(?:section|§)\s*([0-9]+(?:\.[0-9]+)*)'
        match = re.search(pattern, text, re.IGNORECASE)
        
        return match.group(1).strip() if match else ""
    
    def _extract_effective_date(self, text: str) -> str:
        """Extract effective date"""
        pattern = r'(?:effective|commencement)[:\s]*([^.!?\n]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        
        return match.group(1).strip() if match else ""
    
    def _extract_definitions(self, text: str) -> Dict[str, str]:
        """Extract definitions from statute"""
        return self._extract_key_terms(text)
    
    def _extract_prohibitions(self, text: str) -> List[str]:
        """Extract prohibitions from statute"""
        prohibitions = []
        
        pattern = r'(?:prohibited|forbidden|illegal|unlawful)[:\s]*([^.!?\n]+)'
        matches = re.finditer(pattern, text, re.IGNORECASE)
        
        for match in matches:
            prohibitions.append(match.group(1).strip())
        
        return prohibitions
    
    def _extract_requirements(self, text: str) -> List[str]:
        """Extract requirements from statute"""
        requirements = []
        
        pattern = r'(?:required|must|shall)[:\s]*([^.!?\n]+)'
        matches = re.finditer(pattern, text, re.IGNORECASE)
        
        for match in matches:
            requirements.append(match.group(1).strip())
        
        return requirements
    
    def _extract_penalties(self, text: str) -> List[str]:
        """Extract penalties from statute"""
        penalties = []
        
        pattern = r'(?:penalty|fine|punishment)[:\s]*([^.!?\n]+)'
        matches = re.finditer(pattern, text, re.IGNORECASE)
        
        for match in matches:
            penalties.append(match.group(1).strip())
        
        return penalties
    
    def _extract_claims(self, text: str) -> List[str]:
        """Extract claims from case"""
        claims = []
        
        pattern = r'(?:claim|cause of action)[:\s]*([^.!?\n]+)'
        matches = re.finditer(pattern, text, re.IGNORECASE)
        
        for match in matches:
            claims.append(match.group(1).strip())
        
        return claims
    
    def _extract_defenses(self, text: str) -> List[str]:
        """Extract defenses from case"""
        defenses = []
        
        pattern = r'(?:defense|affirmative defense)[:\s]*([^.!?\n]+)'
        matches = re.finditer(pattern, text, re.IGNORECASE)
        
        for match in matches:
            defenses.append(match.group(1).strip())
        
        return defenses
    
    def _extract_case_status(self, text: str) -> str:
        """Extract case status"""
        status_keywords = ['pending', 'settled', 'dismissed', 'active', 'closed']
        
        text_lower = text.lower()
        for status in status_keywords:
            if status in text_lower:
                return status
        
        return "unknown"
