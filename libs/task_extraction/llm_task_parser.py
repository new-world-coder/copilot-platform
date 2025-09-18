"""
LLM Task Parser Module
Extracts structured tasks from legal documents using LLM with regex fallback
"""

import json
import re
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import sys
import os

# Add project root to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from llm.local_llm import run_local_llm
from llm.openai_llm import run_openai_llm
from llm.gemini_llm import run_gemini_llm
from llm.on_prem_llm import run_on_prem_llm

logger = logging.getLogger(__name__)


class TaskExtractor:
    """Extract structured tasks from legal documents"""
    
    def __init__(self, llm_provider: str = "local", llm_model: str = "local"):
        """
        Initialize task extractor
        
        Args:
            llm_provider: LLM provider (local, openai, gemini, onprem)
            llm_model: LLM model name
        """
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self.llm_available = True
        
        # Legal task patterns for regex fallback
        self.task_patterns = {
            'deadline': [
                r'(?:deadline|due|must be completed|shall be filed|must file|due date)[:\s]+([^.\n]+)',
                r'(?:by|before|on|no later than)[:\s]+([^.\n]+)',
                r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
                r'(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{2,4})',
                r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{2,4})',
                r'(\d+\s+(?:days?|weeks?|months?|years?)\s+(?:from|after|following))',
                r'(\d+\s+(?:days?|weeks?|months?|years?)\s+(?:of|from)\s+[^.\n]+)'
            ],
            'action': [
                r'(?:must|shall|will|should|required to|obligated to|agree to)[:\s]+([^.\n]+)',
                r'(?:file|submit|provide|deliver|complete|perform|execute)[:\s]+([^.\n]+)',
                r'(?:action|task|requirement|obligation)[:\s]+([^.\n]+)',
                r'(?:plaintiff|defendant|party|respondent|petitioner)[:\s]+([^.\n]+)',
                r'(?:court|judge|clerk)[:\s]+([^.\n]+)'
            ],
            'priority': [
                r'(?:urgent|immediate|priority|high priority|critical)[:\s]+([^.\n]+)',
                r'(?:as soon as possible|immediately|forthwith)[:\s]+([^.\n]+)'
            ]
        }
    
    async def extract_tasks(self, text: str, document_type: str = "legal") -> Dict[str, Any]:
        """
        Extract tasks from text using LLM with regex fallback
        
        Args:
            text: Input text to extract tasks from
            document_type: Type of document (legal, contract, case_law, etc.)
            
        Returns:
            Dictionary with extracted tasks and metadata
        """
        try:
            # Try LLM extraction first
            if self.llm_available:
                try:
                    llm_result = await self._extract_with_llm(text, document_type)
                    if llm_result and llm_result.get('tasks'):
                        logger.info(f"LLM extracted {len(llm_result['tasks'])} tasks")
                        return llm_result
                except Exception as e:
                    logger.warning(f"LLM extraction failed, falling back to regex: {e}")
                    self.llm_available = False
            
            # Fallback to regex extraction
            regex_result = self._extract_with_regex(text, document_type)
            logger.info(f"Regex extracted {len(regex_result.get('tasks', []))} tasks")
            return regex_result
            
        except Exception as e:
            logger.error(f"Task extraction failed: {e}")
            return {
                "tasks": [],
                "extraction_method": "failed",
                "error": str(e),
                "metadata": {
                    "document_type": document_type,
                    "text_length": len(text),
                    "extraction_timestamp": datetime.now().isoformat()
                }
            }
    
    async def _extract_with_llm(self, text: str, document_type: str) -> Dict[str, Any]:
        """
        Extract tasks using LLM
        
        Args:
            text: Input text
            document_type: Document type
            
        Returns:
            Structured task data
        """
        # Create prompt for task extraction
        prompt = self._create_task_extraction_prompt(text, document_type)
        
        try:
            # Call appropriate LLM based on provider
            if self.llm_provider == "local":
                response = await run_local_llm(prompt)
            elif self.llm_provider == "openai":
                response = await run_openai_llm(prompt, api_key="")  # Will use placeholder
            elif self.llm_provider == "gemini":
                response = await run_gemini_llm(prompt, api_key="")  # Will use placeholder
            elif self.llm_provider == "onprem":
                response = await run_on_prem_llm(prompt, endpoint="http://localhost:8080")
            else:
                raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")
            
            # Parse LLM response
            return self._parse_llm_response(response, text, document_type)
            
        except Exception as e:
            logger.error(f"LLM task extraction failed: {e}")
            raise
    
    def _create_task_extraction_prompt(self, text: str, document_type: str) -> str:
        """Create prompt for LLM task extraction"""
        return f"""You are a legal task extraction AI. Analyze the following {document_type} document and extract all actionable tasks, deadlines, and obligations.

Document Text:
{text[:2000]}...

Please extract tasks in the following JSON format:
{{
    "tasks": [
        {{
            "action": "Specific action to be taken",
            "deadline": "Deadline or due date",
            "priority": "high/medium/low",
            "assignee": "Who is responsible (if mentioned)",
            "context": "Brief context or reason",
            "source_text": "Exact text from document"
        }}
    ],
    "summary": "Brief summary of extracted tasks"
}}

Focus on:
- Deadlines and due dates
- Required actions and obligations
- Filing requirements
- Court orders and directives
- Contract obligations
- Compliance requirements

Return only valid JSON, no additional text."""

    def _parse_llm_response(self, response: str, original_text: str, document_type: str) -> Dict[str, Any]:
        """Parse LLM response into structured format"""
        try:
            # Clean response and extract JSON
            response = response.strip()
            
            # Find JSON in response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                
                # Validate and clean tasks
                tasks = data.get('tasks', [])
                cleaned_tasks = []
                
                for task in tasks:
                    if isinstance(task, dict) and task.get('action'):
                        cleaned_task = {
                            'action': task.get('action', '').strip(),
                            'deadline': task.get('deadline', '').strip(),
                            'priority': task.get('priority', 'medium').strip().lower(),
                            'assignee': task.get('assignee', '').strip(),
                            'context': task.get('context', '').strip(),
                            'source_text': task.get('source_text', '').strip(),
                            'extracted_at': datetime.now().isoformat(),
                            'extraction_method': 'llm'
                        }
                        cleaned_tasks.append(cleaned_task)
                
                return {
                    "tasks": cleaned_tasks,
                    "extraction_method": "llm",
                    "summary": data.get('summary', ''),
                    "metadata": {
                        "document_type": document_type,
                        "text_length": len(original_text),
                        "extraction_timestamp": datetime.now().isoformat(),
                        "llm_provider": self.llm_provider,
                        "llm_model": self.llm_model
                    }
                }
            else:
                raise ValueError("No valid JSON found in LLM response")
                
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            raise
    
    def _extract_with_regex(self, text: str, document_type: str) -> Dict[str, Any]:
        """
        Extract tasks using regex patterns
        
        Args:
            text: Input text
            document_type: Document type
            
        Returns:
            Structured task data
        """
        tasks = []
        
        # Split text into sentences for better pattern matching
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:  # Skip very short sentences
                continue
            
            task_data = {
                'action': '',
                'deadline': '',
                'priority': 'medium',
                'assignee': '',
                'context': sentence,
                'source_text': sentence,
                'extracted_at': datetime.now().isoformat(),
                'extraction_method': 'regex'
            }
            
            # Extract deadlines
            deadline_found = False
            for pattern in self.task_patterns['deadline']:
                match = re.search(pattern, sentence, re.IGNORECASE)
                if match:
                    task_data['deadline'] = match.group(1).strip()
                    deadline_found = True
                    break
            
            # Extract actions
            action_found = False
            for pattern in self.task_patterns['action']:
                match = re.search(pattern, sentence, re.IGNORECASE)
                if match:
                    task_data['action'] = match.group(1).strip()
                    action_found = True
                    break
            
            # Extract priority
            for pattern in self.task_patterns['priority']:
                match = re.search(pattern, sentence, re.IGNORECASE)
                if match:
                    task_data['priority'] = 'high'
                    break
            
            # Only include tasks with either action or deadline
            if action_found or deadline_found:
                tasks.append(task_data)
        
        return {
            "tasks": tasks,
            "extraction_method": "regex",
            "summary": f"Extracted {len(tasks)} tasks using regex patterns",
            "metadata": {
                "document_type": document_type,
                "text_length": len(text),
                "extraction_timestamp": datetime.now().isoformat(),
                "patterns_used": len(self.task_patterns)
            }
        }
    
    def get_task_summary(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get summary statistics for extracted tasks"""
        if not tasks:
            return {"total": 0, "by_priority": {}, "by_assignee": {}}
        
        summary = {
            "total": len(tasks),
            "by_priority": {},
            "by_assignee": {},
            "with_deadlines": 0,
            "with_assignees": 0
        }
        
        for task in tasks:
            # Count by priority
            priority = task.get('priority', 'medium')
            summary["by_priority"][priority] = summary["by_priority"].get(priority, 0) + 1
            
            # Count by assignee
            assignee = task.get('assignee', 'Unassigned')
            if assignee:
                summary["by_assignee"][assignee] = summary["by_assignee"].get(assignee, 0) + 1
            
            # Count tasks with deadlines
            if task.get('deadline'):
                summary["with_deadlines"] += 1
            
            # Count tasks with assignees
            if task.get('assignee'):
                summary["with_assignees"] += 1
        
        return {
            "tasks": tasks,
            "extraction_method": "regex",
            "summary": summary,
            "metadata": {
                "document_type": document_type,
                "total_tasks": len(tasks),
                "extraction_timestamp": datetime.now().isoformat()
            }
        }


# Convenience functions
def extract_tasks_from_text(text: str, 
                          document_type: str = "legal",
                          llm_provider: str = "local") -> Dict[str, Any]:
    """
    Quick function to extract tasks from text
    
    Args:
        text: Input text
        document_type: Document type
        llm_provider: LLM provider
        
    Returns:
        Extracted tasks dictionary
    """
    import asyncio
    
    async def _extract():
        extractor = TaskExtractor(llm_provider)
        return await extractor.extract_tasks(text, document_type)
    
    return asyncio.run(_extract())


def extract_tasks_from_legal_document(text: str, llm_provider: str = "local") -> Dict[str, Any]:
    """Extract tasks specifically from legal documents"""
    return extract_tasks_from_text(text, "legal", llm_provider)


def extract_tasks_from_contract(text: str, llm_provider: str = "local") -> Dict[str, Any]:
    """Extract tasks specifically from contracts"""
    return extract_tasks_from_text(text, "contract", llm_provider)


def extract_tasks_from_case_law(text: str, llm_provider: str = "local") -> Dict[str, Any]:
    """Extract tasks specifically from case law"""
    return extract_tasks_from_text(text, "case_law", llm_provider)


if __name__ == "__main__":
    # Test the task extractor
    import asyncio
    
    async def test_task_extractor():
        """Test task extraction functionality"""
        print("🧪 Testing Task Extractor")
        print("=" * 50)
        
        # Sample legal text
        sample_text = """
        The plaintiff must file a motion for summary judgment within 30 days of the discovery deadline.
        The defendant shall provide all relevant documents by March 15, 2024.
        Both parties are required to attend the mediation session on April 1, 2024.
        The court orders that expert reports must be submitted no later than May 1, 2024.
        """
        
        extractor = TaskExtractor("local")
        
        try:
            result = await extractor.extract_tasks(sample_text, "legal")
            
            print(f"✅ Task extraction successful")
            print(f"Method: {result['extraction_method']}")
            print(f"Tasks found: {len(result['tasks'])}")
            
            for i, task in enumerate(result['tasks'], 1):
                print(f"\nTask {i}:")
                print(f"  Action: {task['action']}")
                print(f"  Deadline: {task['deadline']}")
                print(f"  Priority: {task['priority']}")
                print(f"  Context: {task['context'][:100]}...")
            
            # Test summary
            summary = extractor.get_task_summary(result['tasks'])
            print(f"\n📊 Summary: {summary}")
            
        except Exception as e:
            print(f"❌ Task extraction failed: {e}")
    
    # Run test
    asyncio.run(test_task_extractor())
