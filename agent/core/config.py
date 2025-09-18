"""
Configuration settings for the Copilot Platform Agent
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file with environment variable substitution"""
    config_file = Path(config_path)
    
    if not config_file.exists():
        # Return default configuration if file doesn't exist
        return get_default_config()
    
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Substitute environment variables
        config = substitute_env_vars(config)
        
        return config
    except Exception as e:
        print(f"Error loading config: {e}")
        return get_default_config()


def substitute_env_vars(obj: Any) -> Any:
    """Recursively substitute environment variables in config"""
    if isinstance(obj, dict):
        return {key: substitute_env_vars(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [substitute_env_vars(item) for item in obj]
    elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
        env_var = obj[2:-1]
        return os.getenv(env_var, obj)
    else:
        return obj


def get_default_config() -> Dict[str, Any]:
    """Get default configuration"""
    return {
        "server": {
            "host": "localhost",
            "port": 8000,
            "debug": False
        },
        "llm": {
            "default_provider": "openai",
            "default_model": "gpt-4",
            "providers": {
                "openai": {
                    "api_key": os.getenv("OPENAI_API_KEY"),
                    "models": ["gpt-4", "gpt-3.5-turbo"]
                },
                "anthropic": {
                    "api_key": os.getenv("ANTHROPIC_API_KEY"),
                    "models": ["claude-3-sonnet-20240229"]
                }
            }
        },
        "pdf": {
            "max_file_size": "10MB",
            "supported_formats": ["pdf"]
        },
        "search": {
            "default_provider": "duckduckgo",
            "max_results": 10
        },
        "database": {
            "url": "sqlite:///./copilot.db"
        },
        "rag": {
            "embedding_model": "text-embedding-ada-002",
            "vector_store_path": "./data/vector_store"
        },
        "security": {
            "secret_key": os.getenv("SECRET_KEY", "your-secret-key-here"),
            "access_token_expire_minutes": 30
        },
        "logging": {
            "level": "INFO"
        },
        "tasks": {
            "max_concurrent": 5,
            "timeout": 300
        },
        "cache": {
            "enabled": True,
            "ttl": 3600
        }
    }


# Global config instance
config = load_config()
