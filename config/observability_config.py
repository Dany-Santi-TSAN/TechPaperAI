"""
Docstring for config.observability_config
- Load the config from env.
- Logfire: Pydantic + FastAPI validation and runtime tracing
- LangSmith: LLM call tracing and evaluation
"""

import os
import logfire
from logfire import configure as logfire_configure
from langsmith import Client as LangSmithClient
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class ObservabilityConfig:
    """Central configuration for Logfire and LangSmith"""

    def __init__(self):
        # LogFire settings
        self.logfire_token: Optional[str] = os.getenv("LOGFIRE_TOKEN")
        self.logfire_project: str = os.getenv("LOGFIRE_PROJECT", "agent-mcp-arxiv")

        # LangSmith settings
        self.langsmith_api_key: Optional[str] = os.getenv("LANGSMITH_API_KEY")
        self.langsmith_project: str = os.getenv("LANGSMITH_PROJECT", "agent-mcp-arxiv")
        self.langsmith_endpoint: str = os.getenv(
            "LANGSMITH_ENDPOINT",
            "https://api.smith.langchain.com"
        )

        # Runtime environment
        self.environment: str = os.getenv("ENVIRONMENT", "development")
        self.enable_tracing: bool = os.getenv("ENABLE_TRACING", "true").lower() == "true"

    # === LogFire ===

    def setup_logfire(self) -> None:
        """Configure Logfire for validation and application tracing"""
        try:
            if self.logfire_token:
                logfire_configure(
                    token=self.logfire_token,
                    project_name=self.logfire_project,
                    environment=self.environment,
                    send_to_logfire=self.enable_tracing
                )
            else:
                # Local mode: console logs only
                logfire_configure(send_to_logfire=False, console=True)
                logger.warning("LOGFIRE_TOKEN not set — console logging only")

            # Enable Pydantic instrumentation
            logfire.instrument_pydantic()

            logger.info(
                f"Logfire ready — project={self.logfire_project}, env={self.environment}"
            )

        except Exception as e:
            logger.error(f"Logfire setup failed: {e}")
            raise

    # === LangSmith ===

    def setup_langsmith(self) -> None:
        """Configure LangSmith for LLM tracing"""
        try:
            if not self.langsmith_api_key:
                logger.warning("LANGSMITH_API_KEY not set — LLM tracing disabled")
                os.environ["LANGCHAIN_TRACING_V2"] = "false"
                return

            # LangChain auto-instrumentation
            os.environ["LANGCHAIN_TRACING_V2"] = "true" if self.enable_tracing else "false"
            os.environ["LANGCHAIN_ENDPOINT"] = self.langsmith_endpoint
            os.environ["LANGCHAIN_API_KEY"] = self.langsmith_api_key
            os.environ["LANGCHAIN_PROJECT"] = self.langsmith_project

            # Validate credentials and connectivity
            client = LangSmithClient(
                api_key=self.langsmith_api_key,
                api_url=self.langsmith_endpoint
            )
            client.list_projects(limit=1)

            logger.info(f"LangSmith ready — project={self.langsmith_project}")

        except Exception as e:
            logger.error(f"LangSmith setup failed: {e}")
            raise

    def setup_all(self) -> None:
        """Initialize the full observability stack"""
        logger.info("Setting up observability...")
        self.setup_logfire()
        self.setup_langsmith()
        logger.info("Observability ready")


# === Singleton instance ===
_observability_config: Optional[ObservabilityConfig] = None


def get_observability_config() -> ObservabilityConfig:
    """Return the observability config singleton"""
    global _observability_config
    if _observability_config is None:
        _observability_config = ObservabilityConfig()
    return _observability_config

# === Observability initialization ===

def initialize_observability() -> None:
    """
    Bootstrap observability stack (Logfire + LangSmith).

    Call once at application startup to enable automatic tracing of:
    - Pydantic validations (via Logfire)
    - LLM calls (via LangSmith)

    Raises:
        Exception: If API tokens are invalid or services unreachable
    """
    config = get_observability_config()
    config.setup_all()
