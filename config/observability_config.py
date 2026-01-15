"""
Docstring for config.observability_config
Logfire (Pydantic/FastAPI) + LangSmith (LLM)
"""

import os
import logfire
from logfire import configure as logfire_configure
from langsmith import Client as LangSmithClient
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class ObservabilityConfig:

    def __init__(self):
        # LogFire Config
        self.logfire_token: Optional[str] = os.getenv("LOGFIRE_TOKEN")
        self.logfire_project: str = os.getenv("LOGFIRE_PROJECT", "agent-arxiv")

        # LangSmith config
        self.langsmith_api_key: Optional[str] = os.getenv("LANGSMITH_API_KEY")
        self.langsmith_project: str = os.getenv("LANGSMITH_PROJECT", "agent-arxiv")
        self.langsmith_endpoint: str = os.getenv(
            "LANGSMITH_ENDPOINT",
            "https://api.smith.langchain.com"
        )

        # Environment
        self.environment: str = os.getenv("ENVIRONMENT", "development")
        self.enable_tracing: bool = os.getenv("ENABLE_TRACING", "true").lower() == "true"

        pass
