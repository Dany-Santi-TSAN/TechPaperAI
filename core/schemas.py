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
from pathlib import Path

load_dotenv()

# === Setup Logfire

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
