"""
Task extraction utilities for the Copilot Platform
"""

import re
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class TaskExtractor:
    """Extract tasks and actionable items from text"""
    
    def __init__(self):
        self.task_patterns = [
            r'(?:need to|must|should|have to|required to)\s+([^.!?]+)',
            r'(?:todo|task|action item):\s*([^.!?\n]+)',
            r'(?:deadline|due|by)\s+([^.!?\n]+)',
            r'(?:follow up|follow-up)\s+([^.!?\n]+)',
            r'(?:schedule|book|arrange)\s+([^.!?\n]+)',
            r'(?:call|email|contact)\s+([^.!?\n]+)',
            r'(?:review|check|verify)\s+([^.!?\n]+)',
            r'(?:complete|finish|submit)\s+([^.!?\n]+)',
            r'(?:create|build|develop)\s+([^.!?\n]+)',
            r'(?:update|modify|change)\s+([^.!?\n]+)'
        ]
        
        self.priority_keywords = {
            'high': ['urgent', 'asap', 'immediately', 'critical', 'important'],
            'medium': ['soon', 'this week', 'moderate'],
            'low': ['eventually', 'when possible', 'low priority']
        }
        
        self.time_patterns = [
            r'(?:today|tomorrow|yesterday)',
            r'(?:this|next|last)\s+(?:week|month|year)',
            r'(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            r'(?:january|february|march|april|may|june|july|august|september|october|november|december)',
            r'\d{1,2}/\d{1,2}/\d{2,4}',
            r'\d{1,2}-\d{1,2}-\d{2,4}',
            r'(?:in|within)\s+\d+\s+(?:days?|weeks?|months?|years?)'
        ]
    
    def extract_tasks(self, text: str) -> List[Dict[str, Any]]:
        """Extract tasks from text"""
        tasks = []
        
        # Split text into sentences
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Check for task patterns
            for pattern in self.task_patterns:
                matches = re.finditer(pattern, sentence, re.IGNORECASE)
                for match in matches:
                    task_text = match.group(1).strip()
                    if len(task_text) > 5:  # Filter out very short matches
                        task = self._create_task(task_text, sentence)
                        if task:
                            tasks.append(task)
        
        # Remove duplicates
        tasks = self._remove_duplicates(tasks)
        
        # Sort by priority
        tasks.sort(key=lambda x: self._get_priority_score(x['priority']), reverse=True)
        
        return tasks
    
    def _create_task(self, task_text: str, context: str) -> Optional[Dict[str, Any]]:
        """Create a task object from extracted text"""
        try:
            # Determine priority
            priority = self._determine_priority(context)
            
            # Extract due date
            due_date = self._extract_due_date(context)
            
            # Extract assignee
            assignee = self._extract_assignee(context)
            
            # Extract category
            category = self._extract_category(task_text)
            
            return {
                "id": self._generate_task_id(task_text),
                "text": task_text,
                "priority": priority,
                "due_date": due_date,
                "assignee": assignee,
                "category": category,
                "context": context,
                "created_at": datetime.utcnow().isoformat(),
                "status": "pending"
            }
            
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return None
    
    def _determine_priority(self, text: str) -> str:
        """Determine task priority from context"""
        text_lower = text.lower()
        
        for priority, keywords in self.priority_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return priority
        
        return "medium"
    
    def _extract_due_date(self, text: str) -> Optional[str]:
        """Extract due date from text"""
        text_lower = text.lower()
        
        for pattern in self.time_patterns:
            match = re.search(pattern, text_lower)
            if match:
                return match.group(0)
        
        return None
    
    def _extract_assignee(self, text: str) -> Optional[str]:
        """Extract assignee from text"""
        # Look for patterns like "assign to John", "John should", etc.
        patterns = [
            r'(?:assign to|give to|send to)\s+([A-Za-z\s]+)',
            r'([A-Za-z\s]+)\s+(?:should|must|needs to)',
            r'(?:@|for)\s+([A-Za-z\s]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_category(self, task_text: str) -> str:
        """Extract task category"""
        text_lower = task_text.lower()
        
        categories = {
            "communication": ["email", "call", "message", "contact", "reach out"],
            "development": ["code", "program", "develop", "build", "create", "implement"],
            "documentation": ["write", "document", "record", "note", "log"],
            "meeting": ["meet", "discuss", "present", "demo", "review"],
            "research": ["research", "investigate", "analyze", "study", "find"],
            "admin": ["update", "organize", "schedule", "plan", "arrange"]
        }
        
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return "general"
    
    def _generate_task_id(self, task_text: str) -> str:
        """Generate a unique task ID"""
        import hashlib
        return hashlib.md5(task_text.encode()).hexdigest()[:8]
    
    def _remove_duplicates(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate tasks"""
        seen = set()
        unique_tasks = []
        
        for task in tasks:
            task_key = task['text'].lower().strip()
            if task_key not in seen:
                seen.add(task_key)
                unique_tasks.append(task)
        
        return unique_tasks
    
    def _get_priority_score(self, priority: str) -> int:
        """Get numeric score for priority sorting"""
        scores = {"high": 3, "medium": 2, "low": 1}
        return scores.get(priority, 2)


class MeetingTaskExtractor(TaskExtractor):
    """Specialized task extractor for meeting notes"""
    
    def __init__(self):
        super().__init__()
        self.meeting_patterns = [
            r'(?:action item|ai):\s*([^.!?\n]+)',
            r'(?:follow up|follow-up):\s*([^.!?\n]+)',
            r'(?:next steps?):\s*([^.!?\n]+)',
            r'(?:decided to|agreed to)\s+([^.!?\n]+)',
            r'(?:will|shall)\s+([^.!?\n]+)'
        ]
    
    def extract_meeting_tasks(self, meeting_notes: str) -> List[Dict[str, Any]]:
        """Extract tasks from meeting notes"""
        tasks = []
        
        # Split by common meeting sections
        sections = re.split(r'\n\s*(?:Action Items?|Next Steps?|Follow-ups?|Decisions?)\s*\n', meeting_notes, re.IGNORECASE)
        
        for section in sections:
            section_tasks = self.extract_tasks(section)
            tasks.extend(section_tasks)
        
        return tasks


class EmailTaskExtractor(TaskExtractor):
    """Specialized task extractor for emails"""
    
    def extract_email_tasks(self, email_content: str) -> List[Dict[str, Any]]:
        """Extract tasks from email content"""
        tasks = []
        
        # Extract from subject line
        subject_match = re.search(r'Subject:\s*(.+)', email_content, re.IGNORECASE)
        if subject_match:
            subject_tasks = self.extract_tasks(subject_match.group(1))
            tasks.extend(subject_tasks)
        
        # Extract from body
        body_tasks = self.extract_tasks(email_content)
        tasks.extend(body_tasks)
        
        return tasks


# Convenience functions
def extract_tasks_from_text(text: str) -> List[Dict[str, Any]]:
    """Extract tasks from any text"""
    extractor = TaskExtractor()
    return extractor.extract_tasks(text)


def extract_meeting_tasks(meeting_notes: str) -> List[Dict[str, Any]]:
    """Extract tasks from meeting notes"""
    extractor = MeetingTaskExtractor()
    return extractor.extract_meeting_tasks(meeting_notes)


def extract_email_tasks(email_content: str) -> List[Dict[str, Any]]:
    """Extract tasks from email content"""
    extractor = EmailTaskExtractor()
    return extractor.extract_email_tasks(email_content)
