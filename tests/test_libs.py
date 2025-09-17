"""
Unit tests for libs modules
"""

import pytest
from libs.utils import TextUtils, DataUtils, TimeUtils
from libs.task_extraction import TaskExtractor


class TestTextUtils:
    """Test TextUtils class"""
    
    def test_clean_text(self):
        """Test text cleaning"""
        dirty_text = "  Hello   world  \n\t  "
        clean_text = TextUtils.clean_text(dirty_text)
        assert clean_text == "Hello world"
    
    def test_extract_urls(self):
        """Test URL extraction"""
        text = "Visit https://example.com and http://test.org for more info"
        urls = TextUtils.extract_urls(text)
        assert "https://example.com" in urls
        assert "http://test.org" in urls
    
    def test_word_count(self):
        """Test word counting"""
        text = "Hello world test"
        count = TextUtils.word_count(text)
        assert count == 3


class TestDataUtils:
    """Test DataUtils class"""
    
    def test_safe_json_loads(self):
        """Test safe JSON loading"""
        valid_json = '{"key": "value"}'
        result = DataUtils.safe_json_loads(valid_json)
        assert result == {"key": "value"}
        
        invalid_json = "invalid json"
        result = DataUtils.safe_json_loads(invalid_json, default={})
        assert result == {}


class TestTaskExtractor:
    """Test TaskExtractor class"""
    
    def test_extract_tasks(self):
        """Test task extraction"""
        extractor = TaskExtractor()
        text = "I need to complete the report by Friday. Also, call John about the meeting."
        tasks = extractor.extract_tasks(text)
        
        assert len(tasks) > 0
        assert any("complete the report" in task['text'] for task in tasks)
