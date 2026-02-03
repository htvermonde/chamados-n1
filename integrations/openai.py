# integrations/open_ai.py
"""
Integração OpenAI — chamada à LLM com contador de tokens.

Usa LangChain ChatOpenAI para invocar o modelo e tiktoken para contagem
de tokens (input e output), permitindo monitorar uso e custos.
"""

from typing import Any, Dict, Optional, Tuple


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """
    Conta o número de tokens de um texto para o modelo informado.

    Usa tiktoken com o encoding adequado ao modelo (ex.: o200k_base para gpt-4o).
    """
    try:
        import tiktoken
    except ImportError:
        # Fallback aproximado: ~4 caracteres por token para texto em português/inglês
        return max(0, (len(text) + 3) // 4)

    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


class OpenAIIntegration:
    """
    Cliente OpenAI para o M1: invoca o modelo (ChatOpenAI) e retorna
    conteúdo + uso de tokens (input_tokens, output_tokens, total_tokens).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        temperature: float = 0,
    ):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature

    def invoke(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> Tuple[str, Dict[str, int]]:
        """
        Envia system + user para o modelo e retorna (conteúdo da resposta, uso de tokens).

        Retorno:
            (content, usage) onde usage = { "input_tokens", "output_tokens", "total_tokens" }
        """
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage, SystemMessage

        llm = ChatOpenAI(
            model=self.model,
            api_key=self.api_key,
            temperature=self.temperature,
        )
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        input_tokens = count_tokens(system_prompt + "\n" + user_prompt, self.model)
        response = llm.invoke(messages)
        content = response.content if hasattr(response, "content") else str(response)
        output_tokens = count_tokens(content, self.model)

        # Se a API retornar usage em response_metadata, preferir para output_tokens
        if hasattr(response, "response_metadata"):
            meta = response.response_metadata or {}
            usage_meta = meta.get("token_usage") or meta.get("usage_metadata") or {}
            if usage_meta:
                input_tokens = int(usage_meta.get("input_tokens", input_tokens))
                output_tokens = int(usage_meta.get("output_tokens", output_tokens))

        usage = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
        }
        return content, usage
