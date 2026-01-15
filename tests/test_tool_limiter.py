"""Test ToolCallLimiter guardrail"""

import pytest
import sys
from pathlib import Path


sys.path.append(str(Path(__file__).parent.parent))
from guardrails.tool_call_limiter import ToolCallLimiter
from config.llm_config import LLMConfig


def test_limiter_initialization():
    """Test limiter initializes with correct max"""
    limiter = ToolCallLimiter()
    assert limiter.max_calls_per_tool == 5  # Default from LLMConfig


def test_limiter_allows_calls_within_limit():
    """Test calls are allowed under limit"""
    limiter = ToolCallLimiter()

    for i in range(5):
        assert limiter.can_call("search_papers") == True
        count = limiter.record_call("search_papers")
        assert count == i + 1


def test_limiter_blocks_after_limit():
    """Test calls blocked after limit reached"""
    limiter = ToolCallLimiter()

    # Use up the limit
    for _ in range(5):
        limiter.record_call("search_papers")

    # 6th call should be blocked
    assert limiter.can_call("search_papers") == False


def test_limiter_tracks_per_tool():
    """Test different tools tracked independently"""
    limiter = ToolCallLimiter()

    limiter.record_call("search_papers")
    limiter.record_call("extract_info")

    stats = limiter.get_stats()
    assert stats["search_papers"] == 1
    assert stats["extract_info"] == 1


def test_limiter_reset():
    """Test reset clears all counts"""
    limiter = ToolCallLimiter()

    limiter.record_call("search_papers")
    limiter.record_call("search_papers")

    limiter.reset()

    assert limiter.get_stats() == {}
    assert limiter.can_call("search_papers") == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
