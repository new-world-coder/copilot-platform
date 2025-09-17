"""
Contract analysis utilities for legal vertical
"""

import re
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ContractAnalyzer:
    """Analyze legal contracts and extract key information"""
    
    def __init__(self):
        self.contract_types = [
            'employment', 'service', 'purchase', 'lease', 'license',
            'partnership', 'nda', 'consulting', 'sales', 'distribution'
        ]
        
        self.key_clauses = [
            'termination', 'payment', 'liability', 'indemnification',
            'confidentiality', 'intellectual property', 'governing law',
            'dispute resolution', 'force majeure', 'assignment'
        ]
        
        self.risk_indicators = [
            'unlimited liability', 'penalty', 'liquidated damages',
            'automatic renewal', 'exclusive', 'non-compete',
            'confidentiality breach', 'intellectual property dispute'
        ]
    
    def analyze_contract(self, contract_text: str) -> Dict[str, Any]:
        """Analyze contract and extract key information"""
        try:
            analysis = {
                'contract_type': self._identify_contract_type(contract_text),
                'parties': self._extract_parties(contract_text),
                'key_terms': self._extract_key_terms(contract_text),
                'clauses': self._extract_clauses(contract_text),
                'dates': self._extract_dates(contract_text),
                'financial_terms': self._extract_financial_terms(contract_text),
                'risks': self._identify_risks(contract_text),
                'compliance_issues': self._check_compliance(contract_text),
                'summary': self._generate_summary(contract_text)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing contract: {e}")
            raise
    
    def _identify_contract_type(self, text: str) -> str:
        """Identify the type of contract"""
        text_lower = text.lower()
        
        type_keywords = {
            'employment': ['employee', 'employer', 'salary', 'benefits', 'workplace'],
            'service': ['services', 'service provider', 'deliverables', 'scope of work'],
            'purchase': ['purchase', 'buyer', 'seller', 'goods', 'products'],
            'lease': ['lease', 'tenant', 'landlord', 'rent', 'premises'],
            'license': ['license', 'licensor', 'licensee', 'licensed', 'permit'],
            'nda': ['confidential', 'non-disclosure', 'proprietary', 'secret'],
            'consulting': ['consultant', 'consulting', 'advisory', 'expertise']
        }
        
        scores = {}
        for contract_type, keywords in type_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            scores[contract_type] = score
        
        return max(scores, key=scores.get) if scores else 'unknown'
    
    def _extract_parties(self, text: str) -> List[Dict[str, str]]:
        """Extract contract parties"""
        parties = []
        
        # Look for party definitions
        party_patterns = [
            r'(?:party|company|corporation|llc|inc\.?)\s+([A-Z][A-Za-z\s&,\.]+?)(?:\s+\([^)]+\))?',
            r'([A-Z][A-Za-z\s&,\.]+?)\s+(?:party|company|corporation|llc|inc\.?)',
            r'between\s+([A-Z][A-Za-z\s&,\.]+?)\s+and\s+([A-Z][A-Za-z\s&,\.]+)'
        ]
        
        for pattern in party_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) == 2:
                    parties.extend([
                        {'name': match.group(1).strip(), 'role': 'party'},
                        {'name': match.group(2).strip(), 'role': 'party'}
                    ])
                else:
                    parties.append({
                        'name': match.group(1).strip(),
                        'role': 'party'
                    })
        
        return parties
    
    def _extract_key_terms(self, text: str) -> Dict[str, str]:
        """Extract key terms and definitions"""
        terms = {}
        
        # Look for defined terms
        definition_pattern = r'"([^"]+)"\s*means?\s*([^.!?\n]+)'
        matches = re.finditer(definition_pattern, text, re.IGNORECASE)
        
        for match in matches:
            term = match.group(1).strip()
            definition = match.group(2).strip()
            terms[term] = definition
        
        return terms
    
    def _extract_clauses(self, text: str) -> Dict[str, str]:
        """Extract important clauses"""
        clauses = {}
        
        for clause in self.key_clauses:
            pattern = rf'{clause}[^.!?]*?[.!?]'
            matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
            
            clause_texts = []
            for match in matches:
                clause_texts.append(match.group(0).strip())
            
            if clause_texts:
                clauses[clause] = ' '.join(clause_texts)
        
        return clauses
    
    def _extract_dates(self, text: str) -> List[Dict[str, str]]:
        """Extract important dates"""
        dates = []
        
        date_patterns = [
            r'(?:effective|commencement|start)\s+date[:\s]*([^.!?\n]+)',
            r'(?:expiration|termination|end)\s+date[:\s]*([^.!?\n]+)',
            r'(?:due|deadline)[:\s]*([^.!?\n]+)',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})'
        ]
        
        for pattern in date_patterns:
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
            'payment_amount': r'(?:payment|amount|price|cost)[:\s]*\$?([0-9,]+(?:\.[0-9]{2})?)',
            'payment_terms': r'(?:payment\s+terms?|terms\s+of\s+payment)[:\s]*([^.!?\n]+)',
            'late_fees': r'(?:late\s+fee|penalty)[:\s]*([^.!?\n]+)',
            'currency': r'([A-Z]{3})\s+(?:currency|dollars?)'
        }
        
        for term_type, pattern in patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                financial_terms[term_type] = match.group(1).strip()
        
        return financial_terms
    
    def _identify_risks(self, text: str) -> List[str]:
        """Identify potential risks in the contract"""
        risks = []
        text_lower = text.lower()
        
        for risk in self.risk_indicators:
            if risk in text_lower:
                risks.append(risk)
        
        return risks
    
    def _check_compliance(self, text: str) -> List[str]:
        """Check for compliance issues"""
        compliance_issues = []
        
        # Check for required clauses
        required_clauses = ['governing law', 'jurisdiction', 'entire agreement']
        for clause in required_clauses:
            if clause not in text.lower():
                compliance_issues.append(f"Missing required clause: {clause}")
        
        # Check for problematic language
        problematic_patterns = [
            r'unlimited\s+liability',
            r'waiver\s+of\s+all\s+rights',
            r'automatic\s+renewal\s+without\s+notice'
        ]
        
        for pattern in problematic_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                compliance_issues.append(f"Potentially problematic language: {pattern}")
        
        return compliance_issues
    
    def _generate_summary(self, text: str) -> str:
        """Generate a summary of the contract"""
        # Extract first few sentences as summary
        sentences = re.split(r'[.!?]+', text)
        summary_sentences = [s.strip() for s in sentences[:3] if s.strip()]
        
        return '. '.join(summary_sentences) + '.' if summary_sentences else ""


class ContractComparison:
    """Compare multiple contracts"""
    
    def __init__(self):
        self.analyzer = ContractAnalyzer()
    
    def compare_contracts(self, contracts: List[Dict[str, str]]) -> Dict[str, Any]:
        """Compare multiple contracts"""
        analyses = []
        
        for contract in contracts:
            analysis = self.analyzer.analyze_contract(contract['text'])
            analysis['name'] = contract.get('name', 'Unknown')
            analyses.append(analysis)
        
        comparison = {
            'contracts': analyses,
            'differences': self._find_differences(analyses),
            'common_clauses': self._find_common_clauses(analyses),
            'risk_assessment': self._assess_risks(analyses)
        }
        
        return comparison
    
    def _find_differences(self, analyses: List[Dict]) -> List[Dict]:
        """Find differences between contracts"""
        differences = []
        
        # Compare contract types
        types = [analysis['contract_type'] for analysis in analyses]
        if len(set(types)) > 1:
            differences.append({
                'type': 'contract_type',
                'values': types,
                'description': 'Different contract types identified'
            })
        
        # Compare financial terms
        for analysis in analyses:
            for term, value in analysis['financial_terms'].items():
                # Check if this term differs across contracts
                other_values = [
                    a['financial_terms'].get(term, 'Not specified')
                    for a in analyses if a != analysis
                ]
                
                if value not in other_values:
                    differences.append({
                        'type': f'financial_{term}',
                        'contract': analysis['name'],
                        'value': value,
                        'others': other_values
                    })
        
        return differences
    
    def _find_common_clauses(self, analyses: List[Dict]) -> List[str]:
        """Find clauses common to all contracts"""
        if not analyses:
            return []
        
        first_clauses = set(analyses[0]['clauses'].keys())
        
        for analysis in analyses[1:]:
            first_clauses &= set(analysis['clauses'].keys())
        
        return list(first_clauses)
    
    def _assess_risks(self, analyses: List[Dict]) -> Dict[str, Any]:
        """Assess overall risk across contracts"""
        all_risks = []
        for analysis in analyses:
            all_risks.extend(analysis['risks'])
        
        risk_counts = {}
        for risk in all_risks:
            risk_counts[risk] = risk_counts.get(risk, 0) + 1
        
        return {
            'total_risks': len(all_risks),
            'unique_risks': len(set(all_risks)),
            'risk_frequency': risk_counts,
            'high_risk_contracts': [
                analysis['name'] for analysis in analyses
                if len(analysis['risks']) > 3
            ]
        }
