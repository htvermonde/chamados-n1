import requests
from typing import Optional, Any, Dict


class LibIndexer:
    """
    Cliente para a API LibIndexer, fornecendo métodos para operações CRUD e busca.
    """

    def __init__(
        self,
        base_url: str = "https://llmindexer-api.saiapplications.com",
        api_key: Optional[str] = None,
    ):
        """
        Inicializa o cliente LibIndexer.

        Args:
            base_url (str): URL base da API.
            api_key (str, optional): Chave de API para autenticação no header 'ApiKey'.
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {"ApiKey": self.api_key} if self.api_key else {}

    def query(
        self,
        index_id: str,
        search_query: str,
        quantity: int = 3,
        threshold_similarity: float = 0.4,
        use_chunk_chain: bool = False,
        max_chunk_chain_link: int = 0,
    ) -> Dict[str, Any]:
        """
        Realiza uma busca (query) no índice especificado.
        Correspondente à requisição 'POST query' da imagem.
        """
        url = f"{self.base_url}/api/index/search"
        payload = {
            "indexId": index_id,
            "quantity": quantity,
            "thresholdSimilarity": threshold_similarity,
            "useChunkChain": use_chunk_chain,
            "maxChunkChainLink": max_chunk_chain_link,
            "searchQuery": search_query,
        }

        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_index(self, index_id: str) -> Dict[str, Any]:
        """
        Obtém os detalhes de um índice específico.
        Correspondente à requisição 'GET Get Index' da imagem.
        """
        url = f"{self.base_url}/api/index/{index_id}"

        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def create_index(
        self, name: str, description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cria um novo índice (Operação Create do CRUD).
        """
        url = f"{self.base_url}/api/index"
        payload = {"name": name, "description": description}

        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def update_index(
        self,
        index_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Atualiza um índice existente (Operação Update do CRUD).
        """
        url = f"{self.base_url}/api/index/{index_id}"
        payload = {}
        if name:
            payload["name"] = name
        if description:
            payload["description"] = description

        response = requests.put(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def delete_index(self, index_id: str) -> Dict[str, Any]:
        """
        Remove um índice (Operação Delete do CRUD).
        """
        url = f"{self.base_url}/api/index/{index_id}"

        response = requests.delete(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def list_indexes(self) -> Dict[str, Any]:
        """
        Lista todos os índices disponíveis (Operação Read/List do CRUD).
        """
        url = f"{self.base_url}/api/index"

        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
