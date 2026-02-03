# m1_busca_documental/test_nodes_standalone.py
"""
Como testar um nó por vez — M1 N1 Chamados

Cada nó do LangGraph é uma função que recebe o estado e retorna um partial update.
Para testar um nó isoladamente, você monta um estado "mock" com só o que esse nó
precisa ler, chama a função e inspeciona o retorno.

Uso:
  cd chamados-n1-cursor
  python -m m1_busca_documental.test_nodes_standalone              # roda todos
  python -m m1_busca_documental.test_nodes_standalone api          # só call_libindexr (requer API)
  python -m m1_busca_documental.test_nodes_standalone fetch        # só fetch_local_document
  python -m m1_busca_documental.test_nodes_standalone generate     # só generate_answer
"""

import sys
from typing import Any, Dict

# Garante que a raiz do projeto está no path
import os
from pathlib import Path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from m1_busca_documental.nodes import (
    call_libindexr,
    fetch_local_document,
    generate_answer,
)
from m1_busca_documental.state import AgentState


def test_call_libindexr():
    """Testa só o nó que chama a API libindexr (retorna doc_reference, from_document, best_similarity_score, best_chunks_snippet)."""
    print("\n--- Nó 1: call_libindexr ---")
    state: AgentState = {"user_query": "Como consultar expansão de tipo de avaliação do material?"}
    result = call_libindexr(state)
    print("doc_reference (sourceId):", result.get("doc_reference"))
    print("from_document:", result.get("from_document"))
    print("best_similarity_score:", result.get("best_similarity_score"))
    print("best_chunks_snippet len:", len(result.get("best_chunks_snippet") or ""))
    print("best_chunks_snippet:", result.get("best_chunks_snippet"))
    print("doc_references:", result.get("doc_references"))
    if result.get("api_response"):
        print("api_response (resumido):", type(result["api_response"]), "...")
    print("error:", result.get("error"))
    return result


def test_fetch_local_document():
    """Testa só o nó que lê o documento local e monta retrieved_document (requer source_id no DB n1_chamados)."""
    print("\n--- Nó 2: fetch_local_document ---")
    # Estado mock: doc_reference = source_id (UUID) resolvido via N1ChamadosDB -> kb_id; opcionais para retrieved_document
    state: AgentState = {
        "doc_reference": "c7539b23-a266-4797-ab0c-7018c739c6ce",
        "doc_references": ["c7539b23-a266-4797-ab0c-7018c739c6ce", "542846e4-380a-41b7-b6f9-b190810f2c26"],
        "from_document": "1308ef44-f023-4920-8144-111095aa9be1",
        "best_similarity_score": 0.842549,
        "best_chunks_snippet": 'SAP S4 Hana  Como consultar expansão de  tipo de \r\navaliação do material para centro KB0034986 \r\n\u202f  \r\nProblema: Situações em que o usuário tenta executar um processo de negócio e recebe uma \r\nmensagem informando que o tipo de avaliação exemplo Q.PURCHASE não existe ou qualquer \r\noutro tipo, ou registra um chamado relatando que deseja incluir o tipo de avaliação faltante para o \r\nsistema SAP S/4HANA, com exceção dos casos de VLPOD para o tipo de avaliação OWN. \r\nAmbiente: SAP S4P, SAP BRP e SAP M',
    }
    result = fetch_local_document(state)
    content = result.get("raw_text_content") or ""
    print("Retorno: raw_text_content len =", len(content), "error =", result.get("error"))
    doc = result.get("retrieved_document")
    if doc:
        print("retrieved_document:", doc.get("kb_id"), "-", doc.get("doc_title"), "| score:", doc.get("similarity_score"))
    if content:
        print("Primeiros 200 chars:", content[:200].replace("\n", " ") + "...")
    return result


def test_generate_answer():
    """Testa só o nó da LLM; repassa retrieved_document no retorno (requer OPENAI_API_KEY)."""
    print("\n--- Nó 3: generate_answer ---")
    # Estado mock: pergunta + conteúdo + retrieved_document (repassado no retorno)
    state: AgentState = {
        "user_query": "Como consultar expansão de tipo de avaliação do material para centro?",
        "raw_text_content": (
            "SAP S4 Hana - Como consultar expansão de tipo de avaliação do material para centro KB0034986. "
            "Solução: Verificar na tabela MBEW se existe registro correspondente ao material e ao centro. "
            "Passo 1: Acessar transação ZX_SE16. Passo 2: Digitar o nome da tabela MBEW."
        ),
        "retrieved_document": {
            "kb_id": "KB0034986",
            "doc_title": "Como consultar expansão de tipo de avaliação do material para centro (2)",
            "doc_path": '/mnt/c/Users/htvermonde/OneDrive - Stefanini/Documentos/Codigos/chamados-n1-cursor/documento_busca/KB0034986 - Como consultar expansão de tipo de avaliação do material para centro (2).txt',
            "source_id": "c7539b23-a266-4797-ab0c-7018c739c6ce",
            "from_document": "1308ef44-f023-4920-8144-111095aa9be1",
            "similarity_score": 0.842549,
            "snippet": 'SAP S4 Hana  Como consultar expansão de  tipo de \r\navaliação do material para centro KB0034986 \r\n\u202f  \r\nProblema: Situações em que o usuário tenta executar um processo de negócio e recebe uma \r\nmensagem informando que o tipo de avaliação exemplo Q.PURCHASE não existe ou qualquer \r\noutro tipo, ou registra um chamado relatando que deseja incluir o tipo de avaliação faltante para o \r\nsistema SAP S/4HANA, com exceção dos casos de VLPOD para o tipo de avaliação OWN. \r\nAmbiente: SAP S4P, SAP BRP e SAP M',
        },
    }
    result = generate_answer(state)
    # print("result:", result)

    print("==*"*10)
    print("Resposta da LLM:")
    print("Retorno: final_response len =", len(result.get("final_response") or ""))
    print("doc_path:", result.get("doc_path"))
    print("output tokens:", result.get("token_usage", {}).get("output_tokens", 0))
    print("total tokens:", result.get("token_usage", {}).get("total_tokens", 0))
    print("input tokens:", result.get("token_usage", {}).get("input_tokens", 0))
    print("==*"*10)
    print("retrieved_document:", result.get("retrieved_document"))
    print("==*"*10)    
    print("final_response:", (result.get("final_response") or "")[:300] + "...")
    print("==*"*10)
    if result.get("retrieved_document"):
        print("retrieved_document (repassado):", result["retrieved_document"].get("kb_id"), "-", result["retrieved_document"].get("doc_title"))
    return result


def main():
    which = (sys.argv[1] or "").strip().lower() if len(sys.argv) > 1 else "all"

    print("Testando nós do M1 em modo standalone (estado mock)")

    if which in ("all", "api", "1"):
        test_call_libindexr()
    if which in ("all", "fetch", "2"):
        test_fetch_local_document()
    if which in ("all", "generate", "3"):
        test_generate_answer()

    if which not in ("all", "api", "1", "fetch", "2", "generate", "3"):
        print("\nUso: python -m m1_busca_documental.test_nodes_standalone [api|fetch|generate|all]")
        print("  api      -> só call_libindexr")
        print("  fetch    -> só fetch_local_document")
        print("  generate -> só generate_answer (requer OPENAI_API_KEY)")
        print("  all      -> os três (default)")

    print("\nConcluído.")


if __name__ == "__main__":
    main()
