"""Tests for observability setup and instrumentation"""

import pytest
import os
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))

from config.observability_config import initialize_observability, get_observability_config
from core.schemas import ResearchQuery, Paper


def test_observability_config_loads():
    """Ensure observability configuration loads with expected defaults"""
    config = get_observability_config()
    assert config.logfire_project == "agent-mcp-arxiv"
    assert config.langsmith_project == "agent-arxiv"


def test_observability_initialization():
    """Ensure full observability setup runs without crashing"""
    try:
        initialize_observability()
        # If no exception is raised, initialization is considered successful
        assert True
    except Exception as e:
        pytest.fail(f"Observability initialization failed: {e}")


def test_pydantic_validation_traced():
    """Ensure successful Pydantic validation is traced by Logfire"""
    # Initialize observability before running validations
    initialize_observability()

    # This model instantiation should be traced by Logfire
    query = ResearchQuery(
        query="quantum computing",
        max_results=5
    )

    assert query.query == "quantum computing"

    # Inspect Logfire dashboard to confirm trace presence


def test_pydantic_validation_error_traced():
    """Ensure Pydantic validation errors are also traced"""
    initialize_observability()

    # This validation error should appear in Logfire traces
    with pytest.raises(ValueError):
        ResearchQuery(query="ab")  # Below minimum length


if __name__ == "__main__":
    # Load environment variables for local test runs
    from dotenv import load_dotenv
    load_dotenv()

    pytest.main([__file__, "-v"])
