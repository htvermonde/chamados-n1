# M1 — Motor de Busca Documental (MVP) — N1 Chamados

Pipeline RAG de 2 etapas: **Identificação (API)** → **Recuperação local** → **Síntese (LLM)**.

---

## Como o LangGraph organiza a execução

### StateGraph e estado compartilhado

- O **StateGraph** é um grafo direcionado em que cada **nó** é uma função que recebe o **estado** e retorna um **partial update** (só as chaves que mudaram).
- O **estado** é um único dicionário (`AgentState`) compartilhado por todos os nós. Assim, o nó `call_libindexr` preenche `doc_reference`, e o nó `fetch_local_document` já encontra esse valor no estado sem precisar de variáveis globais.

### O que são as edges (bordas)?

- **Edges** definem a ordem de execução: “quem roda depois de quem”.
- Exemplo: `add_edge("call_libindexr", "fetch_local_document")` significa que `fetch_local_document` **só executa depois** que `call_libindexr` terminar.
- O LangGraph garante que, ao entrar em `fetch_local_document`, o estado já contém o que `call_libindexr` retornou (por exemplo, `doc_reference`).

### Fluxo do M1

```
START → call_libindexr → fetch_local_document → generate_answer → END
```

1. **call_libindexr**: lê `user_query` do estado, chama a API libindexr, escreve `doc_reference` (e opcionalmente `doc_references`, `api_response`) no estado.
2. **fetch_local_document**: lê `doc_reference` do estado, abre o arquivo em `./documento_busca/` (ou `docs_repo`), escreve `raw_text_content` no estado.
3. **generate_answer**: lê `user_query` e `raw_text_content`, chama a LLM com prompt “responda apenas com base no contexto”, escreve `final_response` no estado.
4. **END**: o resultado final é o estado completo (incluindo `final_response`).

### Por que essa arquitetura é mais estável que um script sequencial?

- **Isolamento**: se a API mudar, você altera só o nó `call_libindexr`; o resto do pipeline permanece.
- **Estado explícito**: fica claro o que cada etapa consome e produz (documentado no `AgentState`).
- **Testes**: cada nó pode ser testado isoladamente com um estado mockado.
- **Evolução**: é fácil adicionar ramificações (ex.: se não houver `doc_reference`, ir para um nó de fallback em vez de seguir para `fetch_local_document`).

---

## Configuração

Variáveis de ambiente sugeridas:

| Variável | Descrição |
|----------|-----------|
| `N1_OPENAI_API_KEY` | Chave da OpenAI (GPT-4o). Lida do arquivo `.env` na raiz do projeto (ou variável de ambiente). |
| `M1_INDEX_ID` | ID do índice na API libindexr (onde os KBs foram indexados). |
| `LIBINDEXR_API_KEY` | Chave da API libindexr (se exigida). |
| `LIBINDEXR_BASE_URL` | URL base (default: `https://libindexr.dev.saiapplications.com`). |
| `M1_DOCS_REPO` | Pasta dos documentos locais (default: `./documento_busca`). |

---

## Uso

```bash
# Ativar venv
source venv/bin/activate
pip install -r requirements-m1.txt
# Coloque N1_OPENAI_API_KEY=sk-... no arquivo .env na raiz do projeto
python -m m1_busca_documental.run_example "Sua pergunta aqui"
```

Ou em código:

```python
from m1_busca_documental import rag_graph, AgentState

state: AgentState = {"user_query": "Como consultar expansão de tipo de avaliação do material?"}
result = rag_graph.invoke(state)
print(result["final_response"])
```

---

## Como testar um nó por vez

Cada nó é uma função que recebe o **estado** e retorna um **partial update**. Para testar um nó sozinho:

1. Monte um estado **mock** só com as chaves que esse nó lê.
2. Chame a função do nó com esse estado.
3. Inspecione o retorno (o “partial update”).

### Script de exemplo

```bash
# Testar todos os nós (cada um com estado mock)
python -m m1_busca_documental.test_nodes_standalone

# Só o nó da API (call_libindexr) — requer M1_INDEX_ID e API acessível
python -m m1_busca_documental.test_nodes_standalone api

# Só o nó que lê o arquivo local (fetch_local_document)
python -m m1_busca_documental.test_nodes_standalone fetch

# Só o nó da LLM (generate_answer) — requer OPENAI_API_KEY
python -m m1_busca_documental.test_nodes_standalone generate
```

### Exemplo em código (testar só um nó)

```python
from m1_busca_documental.nodes import fetch_local_document
from m1_busca_documental.state import AgentState

# Estado mock: só o que fetch_local_document precisa ler
state: AgentState = {"doc_reference": "KB0034986 - Como consultar expansão..."}
result = fetch_local_document(state)
print(result["raw_text_content"][:500])  # conteúdo lido do .txt
print(result.get("error"))
```

Assim você valida cada etapa (API, leitura local, LLM) sem rodar o pipeline inteiro.

---

## Estrutura do módulo

- `state.py` — Definição do `AgentState` (TypedDict).
- `config.py` — URLs, pastas e parâmetros (incl. env).
- `nodes.py` — Nós: `call_libindexr`, `fetch_local_document`, `generate_answer`.
- `graph.py` — Montagem do `StateGraph`, edges e `compile()`.
- `run_example.py` — Script de exemplo para rodar o pipeline.
- `test_nodes_standalone.py` — Testar cada nó isoladamente com estado mock.

A chamada à API libindexr é feita **sempre** pelo cliente em `integrations/libindexer.py` (`LibIndexer`). O nó `call_libindexr` usa `LibIndexer.query()`; a URL base e a API key vêm de `m1_busca_documental/config.py` (env `LIBINDEXR_BASE_URL`, `LIBINDEXR_API_KEY`).
