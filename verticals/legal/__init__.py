"""
Legal-specific code and datasets for the Copilot Platform
"""

from .contract_analyzer import ContractAnalyzer
from .legal_document_processor import LegalDocumentProcessor
from .compliance_checker import ComplianceChecker
from .case_law_search import CaseLawSearcher

__all__ = [
    'ContractAnalyzer',
    'LegalDocumentProcessor', 
    'ComplianceChecker',
    'CaseLawSearcher'
]
