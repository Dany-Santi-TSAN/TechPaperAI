"""Guardrail : Tool call limiter to prevent infinite loop"""

import logging
from typing import Dict
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.append(str(Path(__file__).parent.parent))
from config.llm_config import LLMConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class ToolCallLimiter:
    """
    Guardrail to limit tool calls and prevent infinite loops
    Tracks calls per tool across a single query execution
    """

    def __init__(self, config: LLMConfig = None):
        cfg = config or LLMConfig()
        self.max_calls_per_tool = cfg.max_tool_call #max mcp tool call
        self.call_counts: Dict[str, int] = {}
        logger.info(f"ToolCallLimiter initialized with max={self.max_calls_per_tool}")

    def can_call(self, tool_name: str) -> bool:
        """
        Check if a tool can be called (hasn't exceeded limit).

        Args:
            tool_name: Name of the tool to check

        Returns:
            True if tool can be called, False if limit reached
        """
        current_count = self.call_counts.get(tool_name, 0)
        can_proceed = current_count < self.max_calls_per_tool

        if not can_proceed:
            logger.warning(
                f"⚠️ Tool '{tool_name}' blocked: {current_count}/{self.max_calls_per_tool} calls"
            )

        return can_proceed

    def record_call(self, tool_name: str) -> int:
        """
        Record that a tool was called and return new count

        Args:
            tool_name: Name of the tool that was called

        Returns:
            New call count for this tool
        """
        current_count = self.call_counts.get(tool_name, 0) + 1
        self.call_counts[tool_name] = current_count

        logger.info(
            f"🔧 Tool '{tool_name}' called: {current_count}/{self.max_calls_per_tool}"
        )

        return current_count

    def reset(self) -> None:
        """Reset all call counts (for new query)"""
        logger.info("🔄 Resetting tool call counts")
        self.call_counts.clear()
        logger.info("✅ Call counts reset")

    def get_stats(self) -> Dict[str, int]:
        """Get current call counts for all tools for observability"""
        return self.call_counts.copy()
