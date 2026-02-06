# m1_busca_documental/graph.py
"""
Grafo RAG em 2 etapas — LangGraph StateGraph

Como o StateGraph organiza a execução
-------------------------------------
1. O grafo é um fluxo direcionado: cada "nó" é uma função que recebe o estado
   e retorna um dicionário com as chaves a atualizar (partial update).
2. As "edges" (bordas) definem a ordem: quem executa depois de quem.
   Ex.: add_edge("call_libindexr", "fetch_local_document") significa que
   fetch_local_document só roda DEPOIS de call_libindexr terminar.
3. O LangGraph mescla o retorno de cada nó ao estado global; assim,
   fetch_local_document já "vê" doc_reference preenchido por call_libindexr.
4. O ponto de entrada é "__start__" e o de saída é "__end__". O invoke(state)
   percorre: __start__ → call_libindexr → fetch_local_document → generate_answer → __end__.

Por que essa arquitetura é mais estável que um script sequencial?
----------------------------------------------------------------
- Cada etapa está isolada: se a API mudar, você altera só o nó call_libindexr.
- O estado é explícito (TypedDict): fica claro o que cada nó consome e produz.
- Fácil adicionar ramificações depois (ex.: se doc_reference for vazio, ir para
  um nó de fallback em vez de seguir para fetch_local_document).
- Testes unitários: você pode chamar cada nó com um estado mockado.
- Reuso: o mesmo grafo pode ser chamado por API REST, CLI ou outro orquestrador.
"""

from langgraph.graph import StateGraph, START, END

from m1_busca_documental.nodes import (
    call_libindexr,
    fetch_local_document,
    generate_answer,
    forward_to_user,
    forward_to_attendant,
)
from m1_busca_documental.state import AgentState


def decide_next_node(state: AgentState):
    """
    Decide qual o próximo nó após a geração da resposta.
    Se is_kb_relevant for True, vai para forward_to_user.
    Caso contrário, vai para forward_to_attendant.
    """
    if state.get("is_kb_relevant") is True:
        return "forward_to_user"
    return "forward_to_attendant"


def build_rag_graph():
    """
    Constrói e compila o grafo RAG de 2 etapas com encaminhamento condicional.

    Fluxo:
        START → call_libindexr → fetch_local_document → generate_answer
                                                              |
                                           ----------------------------------
                                           |                                |
                                   [Doc Relevante?]                 [Doc Irrelevante?]
                                           |                                |
                                   forward_to_user                  forward_to_attendant
                                           |                                |
                                         END                              END

    Retorno:
        CompiledStateGraph: use .invoke({"user_query": "..."}) para executar.
    """
    # StateGraph(AgentState) indica que o estado do grafo segue o formato AgentState
    graph = StateGraph[AgentState, None, AgentState, AgentState](AgentState)

    # Registrar os nós
    graph.add_node("call_libindexr", call_libindexr)
    graph.add_node("fetch_local_document", fetch_local_document)
    graph.add_node("generate_answer", generate_answer)
    graph.add_node("forward_to_user", forward_to_user)
    graph.add_node("forward_to_attendant", forward_to_attendant)

    # Definir as bordas (edges): ordem de execução
    graph.add_edge(START, "call_libindexr")
    graph.add_edge("call_libindexr", "fetch_local_document")
    graph.add_edge("fetch_local_document", "generate_answer")

    # Borda condicional após generate_answer
    graph.add_conditional_edges(
        "generate_answer",
        decide_next_node,
        {
            "forward_to_user": "forward_to_user",
            "forward_to_attendant": "forward_to_attendant",
        },
    )

    # Bordas finais
    graph.add_edge("forward_to_user", END)
    graph.add_edge("forward_to_attendant", END)

    return graph.compile()


# Instância compilada para uso direto (ex.: from m1_busca_documental.graph import rag_graph)
rag_graph = build_rag_graph()
