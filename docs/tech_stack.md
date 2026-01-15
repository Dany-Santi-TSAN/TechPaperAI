# 📑 Annexe Technique : Projet Research AI & MCP
Ce document centralise les ressources et documentations officielles utilisées pour le développement du pipeline de recherche et d'extraction de papiers arXiv.

## 1. Architecture MCP (Model Context Protocol)
C'est le cœur de la communication entre ton serveur de recherche et ton agent.

Documentation Officielle MCP : https://modelcontextprotocol.io/

FastMCP (Python SDK) : https://github.com/jlowin/fastmcp — Utilisé pour la déclaration simplifiée des tools, resources et prompts.

Spécification des Transports : Concepts de Transport MCP — Essentiel pour comprendre le streamable-http et le SSE.

## 2. Intelligence & Fiabilité (Validation & Evals)
Pour structurer les sorties du LLM et éviter les hallucinations de mapping (ID vs Titre).

PydanticAI (Result Types) : https://ai.pydantic.dev/output/ — La référence pour forcer le LLM à répondre avec un schéma strict.

LLM-as-a-Judge (Evals) : https://ai.pydantic.dev/evals/evaluators/llm-judge/ — Pour automatiser la vérification de la fidélité aux sources.

Pydantic V2 : https://docs.pydantic.dev/latest/ — Pour la validation des données d'entrée des outils.

## 3. Acquisition de Données (ArXiv & PDF)
Les briques qui permettent de passer de la requête au document exploitable.

API ArXiv (Python Wrapper) : https://lukasschwab.me/arxiv.py/index.html — Utilisé dans search_papers.

PyMuPDF4LLM : https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/ — Recommandé pour la conversion PDF vers Markdown (format idéal pour le RAG).

## 4. Frameworks d'Orchestration (Agentic RAG)
Pour construire la logique de "réflexion" de l'agent après l'extraction.

LangGraph : https://langchain-ai.github.io/langgraph/ — Pour gérer les cycles de recherche/extraction/analyse
