"""
LLM Configuration
"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv


load_dotenv()

@dataclass
class LLMConfig:
    """Configuration for LLM."""
    # API
    anthropic_key: str = os.getenv('ANTHROPIC_API_KEY', '')

    # Timeouts
    default_timeout: int = 60
    max_tokens: int = 2024
    # temperature: float = 0.1
    model: str = "claude-haiku-4-5-20251001"
    system_prompt: str = """You are TechPaperAI, specialized in academic paper research.
        When calling tools:
        - Use default parameter values unless user explicitly specifies different values
        - Don't arbitrarily increase max_results beyond the default
        - If user says 'search papers', use default max_results"""

    # safety guardrail
    max_tool_call: int = 2
