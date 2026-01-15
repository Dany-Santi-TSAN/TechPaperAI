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
    max_tool_call: int = 5

@dataclass
class LLMScienceValMod:
    """Configuration for LLM Classifier science/not science"""
    # API
    openrouter_api: str = os.getenv('OPENROUTER_API_KEY', '')

    # Timeouts
    default_timeout: int = 60
    max_tokens: int = 2024
    # temperature: float = 0.1
    model: str = "mistralai/mistral-small-3.2-24b-instruct"
    system_prompt: str = """You are a scientific research query validator.

Determine if the query is a valid SCIENTIFIC RESEARCH question.

Output ONLY this JSON:
{
  "is_scientific": true/false,
  "reason": "Brief explanation"
}"""

    # safety guardrail
    max_retries: int = 3

@dataclass
class LLMScoringPaper:
    """Configuration for LLM Scoring Paper"""
    # API
    openrouter_api: str = os.getenv('OPENROUTER_API_KEY', '')

    # Timeouts
    default_timeout: int = 60
    max_tokens: int = 10000
    temperature: float = 0.1
    model: str = "google/gemini-3-flash-preview"
    system_prompt: str = """You are a research paper relevance evaluator.

Your task: Rate how relevant a paper is to a given research query.

Evaluate on two dimensions:
1. **Relevance (0.0-1.0)**: How well does this paper address the query?
   - 0.0-0.3: Not relevant
   - 0.4-0.6: Somewhat relevant
   - 0.7-0.9: Highly relevant
   - 1.0: Perfect match

2. **Confidence (0.0-1.0)**: How confident are you in this assessment?
   - Based on: publication date, author reputation, abstract quality

Output ONLY a JSON object:
{
  "relevance_score": 0.85,
  "confidence_score": 0.90,
  "justification": "One sentence explaining the scores"
}

No preamble, no markdown, just the JSON."""

    # safety guardrail
    max_retries: int = 2
