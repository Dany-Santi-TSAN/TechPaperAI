"""
Configuration pour LLM
"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv


load_dotenv()

@dataclass
class LLMConfig:
    """Configuration du LLM."""
    # API
    anthropic_key: str = os.getenv('ANTHROPIC_API_KEY', '')

    # Timeouts
    default_timeout: int = 60
    max_tokens: int = 2024
    # temperature: float = 0.1
    model: str = "claude-haiku-4-5-20251001"
