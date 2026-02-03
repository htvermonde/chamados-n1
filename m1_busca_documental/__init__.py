# m1_busca_documental/__init__.py
"""
Módulo M1 — Motor de Busca Documental (MVP) — N1 Chamados

Pipeline RAG de 2 etapas:
  1. Identificação: API libindexr retorna referência do documento.
  2. Recuperação local: leitura do arquivo em ./documento_busca (ou docs_repo).
  3. Síntese: LLM (GPT-4o) gera resposta baseada apenas no contexto local.
"""

from m1_busca_documental.graph import build_rag_graph, rag_graph
from m1_busca_documental.state import AgentState

__all__ = [
    "AgentState",
    "build_rag_graph",
    "rag_graph",
]
