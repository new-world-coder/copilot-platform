"""
General utilities for the Copilot Platform
"""

import hashlib
import json
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
import logging
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)


class TextUtils:
    """Text processing utilities"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove control characters
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        return text.strip()
    
    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """Extract URLs from text"""
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        return re.findall(url_pattern, text)
    
    @staticmethod
    def extract_emails(text: str) -> List[str]:
        """Extract email addresses from text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.findall(email_pattern, text)
    
    @staticmethod
    def extract_phone_numbers(text: str) -> List[str]:
        """Extract phone numbers from text"""
        phone_pattern = r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
        return re.findall(phone_pattern, text)
    
    @staticmethod
    def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
        """Truncate text to maximum length"""
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def word_count(text: str) -> int:
        """Count words in text"""
        return len(text.split())
    
    @staticmethod
    def sentence_count(text: str) -> int:
        """Count sentences in text"""
        sentences = re.split(r'[.!?]+', text)
        return len([s for s in sentences if s.strip()])


class DataUtils:
    """Data processing utilities"""
    
    @staticmethod
    def safe_json_loads(data: str, default: Any = None) -> Any:
        """Safely parse JSON data"""
        try:
            return json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return default
    
    @staticmethod
    def safe_json_dumps(data: Any, default: str = "{}") -> str:
        """Safely serialize data to JSON"""
        try:
            return json.dumps(data, ensure_ascii=False, indent=2)
        except (TypeError, ValueError):
            return default
    
    @staticmethod
    def flatten_dict(d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
        """Flatten nested dictionary"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(DataUtils.flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    @staticmethod
    def merge_dicts(*dicts: Dict) -> Dict:
        """Merge multiple dictionaries"""
        result = {}
        for d in dicts:
            result.update(d)
        return result
    
    @staticmethod
    def remove_none_values(data: Dict) -> Dict:
        """Remove None values from dictionary"""
        return {k: v for k, v in data.items() if v is not None}


class TimeUtils:
    """Time and date utilities"""
    
    @staticmethod
    def utc_now() -> datetime:
        """Get current UTC datetime"""
        return datetime.now(timezone.utc)
    
    @staticmethod
    def utc_timestamp() -> float:
        """Get current UTC timestamp"""
        return time.time()
    
    @staticmethod
    def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format datetime to string"""
        return dt.strftime(format_str)
    
    @staticmethod
    def parse_datetime(date_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
        """Parse datetime from string"""
        try:
            return datetime.strptime(date_str, format_str)
        except ValueError:
            return None
    
    @staticmethod
    def time_ago(dt: datetime) -> str:
        """Get human-readable time ago string"""
        now = TimeUtils.utc_now()
        diff = now - dt
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "just now"


class HashUtils:
    """Hashing utilities"""
    
    @staticmethod
    def md5_hash(data: str) -> str:
        """Generate MD5 hash"""
        return hashlib.md5(data.encode()).hexdigest()
    
    @staticmethod
    def sha256_hash(data: str) -> str:
        """Generate SHA256 hash"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def generate_id(data: str, length: int = 8) -> str:
        """Generate short ID from data"""
        return HashUtils.sha256_hash(data)[:length]


class FileUtils:
    """File handling utilities"""
    
    @staticmethod
    def ensure_directory(path: Union[str, Path]) -> Path:
        """Ensure directory exists"""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @staticmethod
    def get_file_extension(filename: str) -> str:
        """Get file extension"""
        return Path(filename).suffix.lower()
    
    @staticmethod
    def get_file_size(path: Union[str, Path]) -> int:
        """Get file size in bytes"""
        return Path(path).stat().st_size
    
    @staticmethod
    def is_valid_filename(filename: str) -> bool:
        """Check if filename is valid"""
        invalid_chars = '<>:"/\\|?*'
        return not any(char in filename for char in invalid_chars)


class ValidationUtils:
    """Validation utilities"""
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate email address"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Validate URL"""
        pattern = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$'
        return re.match(pattern, url) is not None
    
    @staticmethod
    def is_valid_phone(phone: str) -> bool:
        """Validate phone number"""
        pattern = r'^(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$'
        return re.match(pattern, phone) is not None


class RetryUtils:
    """Retry utilities"""
    
    @staticmethod
    async def retry_async(
        func: callable,
        max_retries: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        exceptions: tuple = (Exception,)
    ) -> Any:
        """Retry async function with exponential backoff"""
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return await func()
            except exceptions as e:
                last_exception = e
                if attempt < max_retries:
                    await asyncio.sleep(delay * (backoff ** attempt))
                else:
                    raise last_exception
        
        raise last_exception
    
    @staticmethod
    def retry_sync(
        func: callable,
        max_retries: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        exceptions: tuple = (Exception,)
    ) -> Any:
        """Retry sync function with exponential backoff"""
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return func()
            except exceptions as e:
                last_exception = e
                if attempt < max_retries:
                    time.sleep(delay * (backoff ** attempt))
                else:
                    raise last_exception
        
        raise last_exception


class ConfigUtils:
    """Configuration utilities"""
    
    @staticmethod
    def load_env_file(file_path: str) -> Dict[str, str]:
        """Load environment variables from file"""
        env_vars = {}
        
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            env_vars[key.strip()] = value.strip()
        except FileNotFoundError:
            logger.warning(f"Environment file {file_path} not found")
        
        return env_vars
    
    @staticmethod
    def get_nested_config(config: Dict, key_path: str, default: Any = None) -> Any:
        """Get nested configuration value"""
        keys = key_path.split('.')
        current = config
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current


# Convenience functions
def clean_text(text: str) -> str:
    """Clean and normalize text"""
    return TextUtils.clean_text(text)


def extract_urls(text: str) -> List[str]:
    """Extract URLs from text"""
    return TextUtils.extract_urls(text)


def generate_id(data: str, length: int = 8) -> str:
    """Generate short ID from data"""
    return HashUtils.generate_id(data, length)


def utc_now() -> datetime:
    """Get current UTC datetime"""
    return TimeUtils.utc_now()


def is_valid_email(email: str) -> bool:
    """Validate email address"""
    return ValidationUtils.is_valid_email(email)


def is_valid_url(url: str) -> bool:
    """Validate URL"""
    return ValidationUtils.is_valid_url(url)
