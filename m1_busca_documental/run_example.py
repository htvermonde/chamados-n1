# m1_busca_documental/run_example.py
"""
Script de exemplo para executar o pipeline RAG do M1.

Uso:
  cd chamados-n1-cursor
  Coloque N1_OPENAI_API_KEY no .env (ou set N1_OPENAI_API_KEY=sk-...)
  set M1_INDEX_ID=...          (opcional; ID do índice na API libindexr)
  set LIBINDEXR_API_KEY=...    (opcional; se a API exigir)
  set LIBINDEXR_BASE_URL=...   (opcional; default: https://libindexr.dev.saiapplications.com)
  python -m m1_busca_documental.run_example

Ou com pergunta customizada:
  python -m m1_busca_documental.run_example "Como consultar expansão de tipo de avaliação do material?"
"""

import os
import sys


def main():
    # Pergunta de exemplo (pode vir do argumento)
    user_query = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "Como consultar expansão de tipo de avaliação do material para centro?"
    )

    # Importar o grafo compilado
    from m1_busca_documental.graph import rag_graph

    print("M1 — Motor de Busca Documental (RAG 2 etapas)")
    print("Pergunta:", user_query)
    print("-" * 60)

    # Estado inicial: apenas user_query; o grafo preenche o resto
    initial_state = {"user_query": user_query}

    # invoke percorre o grafo: call_libindexr → fetch_local_document → generate_answer
    result = rag_graph.invoke(initial_state)

    doc = result.get("retrieved_document")
    if doc:
        print("Documento utilizado:", doc.get("kb_id"), "-", doc.get("doc_title"))
        if doc.get("similarity_score") is not None:
            print("Relevância (similarity):", doc.get("similarity_score"))
    else:
        print("Documento referenciado:", result.get("doc_reference"))
    usage = result.get("token_usage")
    if usage:
        print("Tokens:", usage.get("input_tokens"), "in +", usage.get("output_tokens"), "out =", usage.get("total_tokens"), "total")
    print()
    print("Resposta final:")
    print(result.get("final_response", "(nenhuma)"))
    if result.get("error"):
        print("Erro:", result.get("error"))


if __name__ == "__main__":
    main()
