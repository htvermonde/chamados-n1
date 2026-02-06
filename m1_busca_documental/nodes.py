# m1_busca_documental/nodes.py
"""
Nós do grafo RAG — Módulo M1 N1 Chamados

Cada função neste arquivo é um "nó" do LangGraph. Um nó recebe o estado atual,
faz um trabalho específico e retorna um dicionário com apenas as chaves que
quer atualizar no estado (partial update). O LangGraph mescla esse retorno
ao estado global, e a próxima aresta (edge) encaminha o fluxo para o próximo nó.

Por que essa separação é mais estável que um script sequencial?
- Cada nó pode ser testado isoladamente (unit test).
- Se a API mudar, você altera só call_libindexr; o resto do pipeline permanece.
- Fica explícito o que cada etapa consome e produz (documentado no AgentState).
- Fácil adicionar ramificações (ex.: se não houver doc_reference, ir para um nó de fallback).
"""

import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# Garante que a raiz do projeto está no path para importar integrations.libindexer
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Cliente de busca: usa estritamente o módulo integrations/libindexer.py (LibIndexer)
from integrations.libindexer import LibIndexer

from m1_busca_documental.config import (
    DEFAULT_QUANTITY,
    DEFAULT_THRESHOLD_SIMILARITY,
    DOCS_REPO_PATH,
    INDEX_ID,
    LIBINDEXR_API_KEY,
    LIBINDEXR_BASE_URL,
)
from m1_busca_documental.state import AgentState


# ---------------------------------------------------------------------------
# Nó 1: call_libindexr — Fase de Identificação (API via integrations/libindexer.py)
# ---------------------------------------------------------------------------
def _get_libindexer_client() -> LibIndexer:
    """
    Retorna o cliente LibIndexer de integrations/libindexer.py configurado
    com as variáveis do M1 (LIBINDEXR_BASE_URL, LIBINDEXR_API_KEY).
    Toda chamada à API de busca do M1 passa por este cliente.
    """
    return LibIndexer(
        base_url=LIBINDEXR_BASE_URL.rstrip("/"),
        api_key=LIBINDEXR_API_KEY or None,
    )


def call_libindexr(state: AgentState) -> Dict[str, Any]:
    """
    Consulta a API libindexr para identificar qual documento contém a resposta.
    Delega a chamada POST /api/index/search ao cliente em integrations/libindexer.py (LibIndexer.query).

    Entrada (do estado): user_query
    Saída (atualiza o estado): doc_reference, doc_references, api_response, eventualmente error

    A API espera indexId, searchQuery, quantity, thresholdSimilarity. O retorno
    traz uma lista de chunks/resultados; extraímos a referência do documento
    (nome do arquivo ou ID) para a fase de recuperação local.
    """
    user_query = state.get("user_query") or ""
    if not user_query.strip():
        return {
            "error": "user_query não pode ser vazia.",
            "doc_reference": None,
            "doc_references": None,
        }

    client = _get_libindexer_client()

    try:
        # POST /api/index/search — método query de integrations/libindexer.py
        response = client.query(
            index_id=INDEX_ID
            or "0211f006-78fe-4df2-9b48-9471b0cbf70e",  # deve ser configurado (M1_INDEX_ID)
            search_query=user_query,
            quantity=DEFAULT_QUANTITY,
            threshold_similarity=DEFAULT_THRESHOLD_SIMILARITY,
        )
    except Exception as e:
        return {
            "error": f"Erro ao chamar API libindexr: {e!s}",
            "api_response": None,
            "doc_reference": None,
            "doc_references": None,
        }

    # Formato da API: results[] com fromDocument e chunks[] com { chunk, similarityScore }
    # Escolhemos o documento cujo chunk tem o maior similarityScore
    doc_reference = None
    from_document = None
    best_similarity_score = None
    best_chunks_snippet = None
    doc_references = []
    best_result_chunks: list = []

    results = response.get("results")
    if isinstance(results, list):
        best_score = -1.0
        for res in results:
            res_from_doc = res.get("fromDocument")
            chunks = res.get("chunks")
            if not isinstance(chunks, list):
                continue
            for ch in chunks:
                chunk_data = ch.get("chunk")
                score = ch.get("similarityScore")
                if not isinstance(chunk_data, dict):
                    continue
                sid = chunk_data.get("sourceId")
                if sid and sid not in doc_references:
                    doc_references.append(str(sid))
                if score is not None and float(score) > best_score:
                    best_score = float(score)
                    doc_reference = str(chunk_data.get("sourceId") or "")
                    from_document = str(res_from_doc) if res_from_doc else None
                    best_similarity_score = best_score
                    # Guardar chunks do melhor resultado para montar snippet
                    best_result_chunks = list(chunks)

        # Snippet: concatena rawContent dos chunks do melhor resultado (até ~500 chars)
        if best_result_chunks:
            parts = []
            total = 0
            for ch in best_result_chunks:
                c = ch.get("chunk") if isinstance(ch, dict) else None
                raw = (c.get("rawContent") or "").strip() if isinstance(c, dict) else ""
                if raw and total < 500:
                    parts.append(raw[: 500 - total])
                    total += len(parts[-1])
                    if total >= 500:
                        break
            if parts:
                best_chunks_snippet = " ".join(parts).strip()[:500]

    return {
        "api_response": response,
        "doc_reference": doc_reference,
        "doc_references": doc_references if doc_references else None,
        "from_document": from_document,
        "best_similarity_score": best_similarity_score,
        "best_chunks_snippet": best_chunks_snippet,
        "error": None,
    }


# ---------------------------------------------------------------------------
# Nó 2: fetch_local_document — Fase de Recuperação Local (Fonte da Verdade)
# ---------------------------------------------------------------------------
def _find_local_file(doc_reference: str, docs_path: str) -> Optional[str]:
    """
    Encontra o arquivo .txt no repositório local correspondente à referência.

    Estratégias:
    1) doc_reference já é um nome de arquivo (com ou sem extensão) → busca por nome.
    2) Contém um número de KB (ex.: KB0034986) → lista arquivos e filtra pelo KB.
    """
    if not doc_reference or not os.path.isdir(docs_path):
        return None

    doc_ref_clean = (doc_reference or "").strip()
    if not doc_ref_clean:
        return None

    # Remove extensão se vier na referência
    base_ref = re.sub(r"\.(txt|pdf)$", "", doc_ref_clean, flags=re.IGNORECASE)

    # 1) Busca exata por nome (com .txt)
    for name in os.listdir(docs_path):
        if not name.endswith(".txt"):
            continue
        base_name = re.sub(r"\.txt$", "", name, flags=re.IGNORECASE)
        if base_name == base_ref or base_ref in base_name or base_name in base_ref:
            return os.path.join(docs_path, name)

    # 2) Extrai possível código KB (ex.: KB0017882, KB0034986)
    kb_match = re.search(r"KB\d+", doc_ref_clean, re.IGNORECASE)
    if kb_match:
        kb_code = kb_match.group(0).upper()
        for name in os.listdir(docs_path):
            if not name.endswith(".txt"):
                continue
            if kb_code.upper() in name.upper():
                return os.path.join(docs_path, name)

    return None


def fetch_local_document(state: AgentState) -> Dict[str, Any]:
    """
    Localiza o documento correto usando o source_id (doc_reference) contra a tabela n1_chamados,
    e então lê o arquivo físico correspondente na pasta de documentos.

    Entrada (do estado): doc_reference (source_id), doc_references (lista de source_ids)
    Saída (atualiza o estado): raw_text_content, kb_id, eventualmente error
    """
    from database.n1_chamados import N1ChamadosDB

    doc_reference = state.get("doc_reference")
    if not doc_reference:
        return {
            "error": "Nenhum doc_reference (source_id) fornecido para busca local.",
        }

    # 1. Consulta o "banco de dados" (versão beta) para converter source_id em kb_id
    db = N1ChamadosDB()
    records = db.get_by_source_id(str(doc_reference))

    if not records:
        return {
            "error": f"Nenhum registro encontrado no banco n1_chamados para source_id: {doc_reference}",
        }

    # Pegamos o kb_id do primeiro registro encontrado
    kb_id = records[0].get("kb_id")
    if not kb_id:
        return {
            "error": f"Registro encontrado para {doc_reference}, mas kb_id está vazio.",
        }

    print(f"Resolvido: source_id {doc_reference} -> kb_id {kb_id}")

    # 2. Busca o arquivo local (.txt) que contém o kb_id no nome
    file_path = _find_local_file(kb_id, DOCS_REPO_PATH)

    if not file_path or not os.path.isfile(file_path):
        return {
            "error": f"Documento local não encontrado para KB: {kb_id} (pasta: {DOCS_REPO_PATH})",
        }

    # 3. Leitura do conteúdo
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            raw_text_content = f.read()
    except Exception as e:
        return {
            "error": f"Erro ao ler arquivo local {file_path}: {e!s}",
        }

    # 4. Documento retornado ao usuário (junto com a resposta da LLM)
    doc_title = os.path.splitext(os.path.basename(file_path))[0]
    retrieved_document = {
        "kb_id": kb_id,
        "doc_title": doc_title,
        "doc_path": file_path,
        "source_id": str(doc_reference),
        "from_document": state.get("from_document"),
        "similarity_score": state.get("best_similarity_score"),
        "snippet": state.get("best_chunks_snippet"),
    }

    return {
        "raw_text_content": raw_text_content,
        "kb_id": kb_id,
        "retrieved_document": retrieved_document,
        "error": None,
    }


# ---------------------------------------------------------------------------
# Nó 3: generate_answer — Fase de Síntese (LLM)
# ---------------------------------------------------------------------------
def _load_generate_answer_prompt(version: str = "v3") -> Dict[str, Any]:
    """Carrega o prompt do agente generate_answer a partir de Agents/generate_answer_{version}.yaml."""
    import yaml

    agents_dir = Path(__file__).resolve().parent / "Agents"
    prompt_path = agents_dir / f"generate_answer_{version}.yaml"
    if not prompt_path.is_file():
        # Fallback para v2 se v3 não existir por algum motivo
        prompt_path = agents_dir / "generate_answer_v2.yaml"

    if not prompt_path.is_file():
        raise FileNotFoundError(f"Prompt não encontrado: {prompt_path}")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _parse_llm_response(content: str) -> Tuple[bool, str]:
    """
    Extrai a classificação (RELEVANTE/IRRELEVANTE) e limpa o texto da resposta.
    Esperado: 'CLASSIFICACAO: RELEVANTE\n\nResposta...'
    """
    is_relevant = True
    clean_content = content.strip()

    match = re.search(
        r"CLASSIFICACAO:\s*(RELEVANTE|IRRELEVANTE)", clean_content, re.IGNORECASE
    )
    if match:
        label = match.group(1).upper()
        is_relevant = label == "RELEVANTE"
        # Remove a linha da classificação do texto final
        clean_content = re.sub(
            r"CLASSIFICACAO:.*?\n+", "", clean_content, flags=re.IGNORECASE
        ).strip()

    return is_relevant, clean_content


def _call_llm_for_answer(state: AgentState) -> Tuple[str, Optional[Dict[str, int]]]:
    """Faz a chamada à LLM usando o prompt v3 que inclui classificação."""
    from m1_busca_documental.config import OPENAI_API_KEY, LLM_MODEL
    from integrations.openai import OpenAIIntegration

    user_query = (state.get("user_query") or "").strip()
    raw_text_content = state.get("raw_text_content") or ""

    prompt_config = _load_generate_answer_prompt("v3")
    system_prompt = (prompt_config.get("system_prompt") or "").strip()
    user_template = (prompt_config.get("user_prompt_template") or "").strip()
    max_chars = int(prompt_config.get("max_context_chars") or 120000)

    raw_slice = raw_text_content[:max_chars]
    user_prompt = user_template.replace("{{raw_text_content}}", raw_slice).replace(
        "{{user_query}}", user_query
    )

    client = OpenAIIntegration(
        api_key=OPENAI_API_KEY,
        model=LLM_MODEL,
        temperature=0,
    )
    return client.invoke(system_prompt=system_prompt, user_prompt=user_prompt)


def generate_answer(state: AgentState) -> Dict[str, Any]:
    """
    Gera a resposta final usando a LLM (GPT-4o).
    Agora avalia se o KB é coerente; se não for, gera uma sugestão e sinaliza para consultor.

    Entrada (do estado): user_query, raw_text_content
    Saída (atualiza o estado): final_response, is_kb_relevant, is_suggestion, needs_consultant
    """
    from m1_busca_documental.config import OPENAI_API_KEY

    doc_path = state.get("doc_path") or ""
    err = state.get("error")

    if err:
        return {
            "final_response": f"Não foi possível processar a solicitação: {err}",
            "is_kb_relevant": False,
            "needs_consultant": True,
        }

    if not state.get("raw_text_content"):
        return {
            "final_response": "Nenhum documento encontrado. Por favor, aguarde enquanto um consultor analisa sua dúvida.",
            "is_kb_relevant": False,
            "is_suggestion": True,
            "needs_consultant": True,
        }

    if not OPENAI_API_KEY:
        return {
            "final_response": "[Configuração] API Key ausente.",
            "error": "API Key ausente.",
        }

    try:
        # 1. Chamada à LLM (delegada para função interna)
        raw_response, token_usage = _call_llm_for_answer(state)

        # 2. Parse da resposta (delegada para função interna)
        is_relevant, final_response = _parse_llm_response(raw_response)

    except Exception as e:
        final_response = f"Erro ao gerar resposta com a LLM: {e!s}"
        token_usage = None
        is_relevant = False

    # 3. Retorno do estado com as novas flags de controle
    return {
        "final_response": final_response,
        "is_kb_relevant": is_relevant,
        "is_suggestion": not is_relevant,
        "needs_consultant": not is_relevant,  # Se não for relevante, vai para o consultor
        "retrieved_document": state.get("retrieved_document"),
        "token_usage": token_usage,
        "doc_path": doc_path,
    }


# ---------------------------------------------------------------------------
# Nó 4: forward_to_user — Encaminhamento para o usuário
# ---------------------------------------------------------------------------
def forward_to_user(state: AgentState) -> Dict[str, Any]:
    """
    Nó acionado quando a resposta foi encontrada no KB com sucesso.
    Pode ser usado para logs, métricas ou integrações de saída direta.
    """
    print(">>> Fluxo: Encaminhando resposta do KB para o usuário.")
    return {"status": "forwarded_to_user"}


# ---------------------------------------------------------------------------
# Nó 5: forward_to_attendant — Encaminhamento para atendente
# ---------------------------------------------------------------------------
def forward_to_attendant(state: AgentState) -> Dict[str, Any]:
    """
    Nó acionado quando a pergunta não foi respondida pelo KB.
    Encaminha para um consultor/atendente humano.
    """
    print(">>> Fluxo: Pergunta sem resposta no KB. Encaminhando para atendente.")
    return {"status": "forwarded_to_attendant"}
