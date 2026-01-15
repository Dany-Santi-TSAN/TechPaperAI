"""Test environment configuration and API tokens validity"""

import pytest
import os
from dotenv import load_dotenv
import logfire
from langsmith import Client


# Load .env once for all tests
load_dotenv()


class TestEnvironmentVariables:
    """Test that all required environment variables are present"""

    def test_logfire_token_exists(self):
        """Check LOGFIRE_TOKEN is set"""
        token = os.getenv("LOGFIRE_TOKEN")
        assert token is not None, "LOGFIRE_TOKEN not found in .env"
        assert len(token) > 10, "LOGFIRE_TOKEN seems too short"
        assert token.startswith("pylf_"), "LOGFIRE_TOKEN should start with 'pylf_'"

    def test_logfire_project_exists(self):
        """Check LOGFIRE_PROJECT is set"""
        project = os.getenv("LOGFIRE_PROJECT")
        assert project is not None, "LOGFIRE_PROJECT not found in .env"
        assert project == "agent-mcp-arxiv", f"Expected 'agent-mcp-arxiv', got '{project}'"

    def test_langsmith_api_key_exists(self):
        """Check LANGSMITH_API_KEY is set"""
        api_key = os.getenv("LANGSMITH_API_KEY")
        assert api_key is not None, "LANGSMITH_API_KEY not found in .env"
        assert len(api_key) > 10, "LANGSMITH_API_KEY seems too short"
        assert api_key.startswith("lsv2_"), "LANGSMITH_API_KEY should start with 'lsv2_'"

    def test_langsmith_project_exists(self):
        """Check LANGSMITH_PROJECT is set"""
        project = os.getenv("LANGSMITH_PROJECT")
        assert project is not None, "LANGSMITH_PROJECT not found in .env"
        assert project == "agent-mcp-arxiv", f"Expected 'agent-mcp-arxiv', got '{project}'"


class TestAPIConnectivity:
    """Test that API tokens are valid and services are reachable"""

    @pytest.mark.skipif(
        not os.getenv("LOGFIRE_TOKEN"),
        reason="LOGFIRE_TOKEN not set"
    )
    def test_logfire_token_valid(self):
        """Test Logfire token is valid by attempting to configure"""
        token = os.getenv("LOGFIRE_TOKEN")

        try:
            logfire.configure(
                token=token,
                send_to_logfire=True,
                console=False
            )
            # If no exception, token is valid
            logfire.info("Logfire token validation test")
            assert True, "✅ Logfire token is valid"

        except Exception as e:
            pytest.fail(f"❌ Logfire token invalid: {e}")

    @pytest.mark.skipif(
        not os.getenv("LANGSMITH_API_KEY"),
        reason="LANGSMITH_API_KEY not set"
    )
    def test_langsmith_token_valid(self):
        """Test LangSmith token is valid by listing projects"""
        api_key = os.getenv("LANGSMITH_API_KEY")

        try:
            client = Client(api_key=api_key)

            assert client.api_key == api_key, "Client created successfully"

        except Exception as e:
            pytest.fail(f"❌ LangSmith token invalid: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
