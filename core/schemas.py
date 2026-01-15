"""
Pydantic Schemas
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
import logfire
from typing import Optional, Any
from datetime import datetime
from enum import Enum
import os
from dotenv import load_dotenv
import sys

load_dotenv()

# === Setup Logfire ===

logfire.configure()
logfire.instrument_pydantic()

# === Safety ===

class SafetyStatus(str, Enum):
    SAFE = "safe"
    UNSAFE = "unsafe"
    REVIEW_NEEDED = "review_needed"

class SafetyCheck(BaseModel):
    status: SafetyStatus
    reason: Optional[str] = None
    categories_flagged: list[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0,ge=0.0, le=1.0)

    model_config = ConfigDict(
        use_enum_values=True
        ,str_strip_whitespace=True
    )

# === Input ===

class ResearchQuery(BaseModel):
    """User research query with basic validation rules"""

    # User query text with length constraints
    query: str = Field(..., min_length=3, max_length=500)
    max_results: int = Field(default=5, ge=1, le=10)

    @field_validator('query')
    @classmethod
    def query_not_empty(cls, v: str) -> str:
        """Valide que le query n'est pas vide après strip"""
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Query cannot be empty or whitespace only")
        return cleaned

    model_config = ConfigDict(
        str_strip_whitespace=True, # Automatically strip leading/trailing whitespace from all strings
        validate_assignment=True  # Re-run validation when fields are modified after instantiation
    )

# === OUTPUT ===

class Paper(BaseModel):
    """
    ArXiv paper with enriched metadata
    Optional scoring fields are included for cost / relevance A/B testing
    """
    arxiv_id: str = Field(..., alias="id") # ArXiv identifier (mapped from external field "id")
    title: str
    authors: list[str]
    summary: str
    pdf_url: str
    published: str
    query_date: str

    # Optional relevance scoring (used for ranking and cost-related A/B tests)
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    relevance_justification: Optional[str] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)

    @field_validator('authors')
    @classmethod
    def authors_not_empty(cls, v: list[str]) -> list[str]:
        """Log a warning if no authors are provided (non-blocking validation)"""
        if not v:
            import logging
            logging.warning("Paper has no authors listed")
        return v

    model_config = ConfigDict(
        populate_by_name=True,  # Allow alias "id" → "arxiv_id"
        validate_assignment=True, # Re-validate fields if modified after model creation
        str_strip_whitespace=True # Automatically strip leading/trailing whitespace from all strings
    )


class ResearchOutput(BaseModel):
    """Final research output including results, safety signals, and observability metrics"""
    papers: list[Paper]
    total_found: int
    query_used: str
    safety_check: SafetyCheck # 1. Safety and content validation result
    is_scientific: bool # 2. Scientific classification signal
    scientific_reason: Optional[str] = None

    # Métriques observabilité
    execution_time: float = Field(..., description="Temps total en secondes")
    tokens_used: Optional[int] = None
    estimated_cost: Optional[float] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

    model_config = ConfigDict(
        validate_assignment=True
    )

# ============= LANGGRAPH STATE =============

class AgentState(BaseModel):
    """
    Shared state used across the LangGraph execution.
    Stores all intermediate data produced by the agent pipeline.
    """
    # Input
    query: str
    max_results: int = 5
    # Conversation or tool interaction history
    messages: list[dict[str, Any]] = Field(default_factory=list)

    # Validation steps
    safety_check: Optional[SafetyCheck] = None
    is_scientific: Optional[bool] = None
    scientific_reason: Optional[str] = None
    validated_query: Optional[str] = None # Normalized and validated version of the user query

    # Search results
    papers: list[Paper] = Field(default_factory=list)

    # Scoring (optional)
    scoring_enabled: bool = False # Enable relevance / confidence scoring

    # Error handling
    errors: list[str] = Field(default_factory=list)
    retry_count: int = 0 # Number of retries performed by the agent

    # Metrics & observability
    start_time: float = Field(default_factory=lambda: datetime.now().timestamp()) # Timestamp agent execution started (epoch seconds)
    tokens_used: int = 0

    model_config = ConfigDict(
        arbitrary_types_allowed=True
        ,validate_assignment=True
    )
