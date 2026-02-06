# m1_busca_documental/state.py
"""
Definição do Estado do Grafo (AgentState) — Módulo M1 N1 Chamados

Por que TypedDict?
-----------------
No LangGraph, todos os nós do grafo compartilham um único objeto de estado.
O TypedDict define quais chaves existem e quais tipos elas têm, garantindo
que cada nó leia e escreva dados de forma previsível. Assim, o nó "call_libindexr"
preenche doc_reference, e o nó "fetch_local_document" já encontra esse valor
disponível no estado sem precisar de variáveis globais ou callbacks.
"""

from typing import Any, Dict, List, Optional, TypedDict


class AgentState(TypedDict, total=False):
    """
    Estado compartilhado do pipeline RAG em 2 etapas.

    total=False indica que todas as chaves são opcionais na entrada;
    o grafo vai preenchendo cada uma conforme avança.

    Campos:
    - user_query: pergunta original do usuário (entrada do pipeline).
    - doc_reference: sourceId do documento escolhido (API libindexr).
    - doc_references: lista de source_ids retornados pela API.
    - from_document: documentId/fromDocument do melhor resultado (API).
    - best_similarity_score: maior similarityScore do documento escolhido.
    - best_chunks_snippet: trecho opcional dos rawContent dos chunks (para exibição).
    - raw_text_content: conteúdo integral do documento lido da pasta local (fonte da verdade).
    - kb_id: identificador KB do documento (mapeado via n1_chamados).
    - retrieved_document: documento retornado ao usuário (kb_id, título, path, score, etc.).
    - final_response: resposta gerada pela LLM com base apenas no contexto.
    - token_usage: uso de tokens da chamada LLM (input_tokens, output_tokens, total_tokens).
    - error: mensagem de erro, se algum nó falhar (útil para debugging).
    - api_response: resposta bruta da API (opcional, para inspeção).
    """

    user_query: str
    doc_reference: Optional[str]
    doc_references: Optional[List[Any]]
    from_document: Optional[str]
    best_similarity_score: Optional[float]
    best_chunks_snippet: Optional[str]
    raw_text_content: Optional[str]
    kb_id: Optional[str]
    retrieved_document: Optional[Dict[str, Any]]
    final_response: Optional[str]
    token_usage: Optional[Dict[str, int]]
    error: Optional[str]
    api_response: Optional[Any]
    is_kb_relevant: Optional[bool]
    is_suggestion: Optional[bool]
    needs_consultant: Optional[bool]
    status: Optional[str]
