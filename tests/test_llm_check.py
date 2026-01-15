"""Test LLM configurations with OpenRouter"""

import pytest
import os
import json
from dotenv import load_dotenv
from openai import OpenAI
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from config.llm_config import LLMScienceValMod, LLMScoringPaper

load_dotenv()


class TestScientificValidationLLM:
    """Test Mistral Small for scientific validation"""

    @pytest.fixture
    def client(self):
        """OpenRouter client"""
        config = LLMScienceValMod()
        return OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=config.openrouter_api
        )

    @pytest.fixture
    def config(self):
        return LLMScienceValMod()

    def test_scientific_query_valid(self, client, config):
        """Test with valid scientific query"""
        query = "quantum computing error correction methods"

        response = client.chat.completions.create(
            model=config.model,
            messages=[
                {"role": "system", "content": config.system_prompt},
                {"role": "user", "content": f"Query: {query}"}
            ],
            max_tokens=config.max_tokens,
            timeout=config.default_timeout
        )

        result = response.choices[0].message.content
        print(f"\n✅ Scientific query test:")
        print(f"Query: {query}")
        print(f"Response: {result}")

        # Parse JSON
        data = json.loads(result)
        assert "is_scientific" in data
        assert "reason" in data
        assert data["is_scientific"] == True

    def test_scientific_query_invalid(self, client, config):
        """Test with non-scientific query"""
        query = "best pizza recipe in New York"

        response = client.chat.completions.create(
            model=config.model,
            messages=[
                {"role": "system", "content": config.system_prompt},
                {"role": "user", "content": f"Query: {query}"}
            ],
            max_tokens=config.max_tokens,
            timeout=config.default_timeout
        )

        result = response.choices[0].message.content
        print(f"\n❌ Non-scientific query test:")
        print(f"Query: {query}")
        print(f"Response: {result}")

        # Parse JSON
        data = json.loads(result)
        assert data["is_scientific"] == False


class TestPaperScoringLLM:
    """Test Gemini Flash for paper scoring"""

    @pytest.fixture
    def client(self):
        """OpenRouter client"""
        config = LLMScoringPaper()
        return OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=config.openrouter_api
        )

    @pytest.fixture
    def config(self):
        return LLMScoringPaper()

    def test_paper_scoring_relevant(self, client, config):
        """Test scoring with relevant paper"""
        query = "quantum computing"
        paper_title = "Quantum Error Correction in Superconducting Qubits"
        paper_summary = "We demonstrate improved error correction techniques for quantum computers using superconducting circuits."

        prompt = f"""Query: {query}

Paper Title: {paper_title}
Paper Summary: {paper_summary}"""

        response = client.chat.completions.create(
            model=config.model,
            messages=[
                {"role": "system", "content": config.system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            timeout=config.default_timeout
        )

        result = response.choices[0].message.content
        print(f"\n📊 Paper scoring test:")
        print(f"Query: {query}")
        print(f"Paper: {paper_title}")
        print(f"Response: {result}")

        # Parse JSON
        data = json.loads(result)
        assert "relevance_score" in data
        assert "confidence_score" in data
        assert "justification" in data
        assert 0.0 <= data["relevance_score"] <= 1.0
        assert 0.0 <= data["confidence_score"] <= 1.0
        assert data["relevance_score"] > 0.7  # Should be highly relevant


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
