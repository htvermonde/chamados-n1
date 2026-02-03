import os
import requests

from app.core.config import settings


class LlmIndexEngine:
    def __init__(
        self,
    ):
        """
        Inicializa a engine do LlmIndexer.

        Args:
            doc_hash (str, optional): Hash do documento/índice. Se não informado, usa do settings.
            api_key (str, optional): Chave de API (Header: ApiKey). Se não informado, usa do settings.
        """
        self.doc_hash = "H4b5963a3bdc8485cbe92fcaf493999c3"
        self.api_key = settings.LLM_INDEX_API_KEY
        self.base_url = "https://llmindexer-api.saiapplications.com"
        self.headers = {"ApiKey": self.api_key}

    def list_files(self):
        """
        Lista os arquivos associados ao hash do documento.

        Endpoint esperado: GET /api/index/{hash}/files
        """
        url = f"{self.base_url}/api/index/{self.doc_hash}/files"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def upload_file(self, file_path: str):
        """
        Faz upload de um arquivo para o índice.

        Endpoint: POST /api/index/{hash}/files/upload
        Body: Files (multipart/form-data)
        """
        url = f"{self.base_url}/api/index/{self.doc_hash}/files/upload"

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

        filename = os.path.basename(file_path)

        # 'Files' é a chave especificada no prompt para o corpo da requisição
        with open(file_path, "rb") as f:
            files = {"Files": (filename, f)}
            response = requests.post(url, headers=self.headers, files=files)

        response.raise_for_status()
        return response.json()

    def get_file_info(self, file_id: str):
        """
        Obtém informações detalhadas de um arquivo específico.

        Endpoint esperado: GET /api/index/{hash}/files/{file_id}
        """
        url = f"{self.base_url}/api/index/{self.doc_hash}/files/{file_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_rag_details(self, question: str):
        """
        Obtém detalhes do RAG (Retrieve Augmented Generation) com base em uma pergunta.

        Endpoint esperado: POST /api/index/{hash}/search (Suposição padrão REST)
        """
        # Assumindo endpoint de busca/query
        url = f"{self.base_url}/api/index/{self.doc_hash}/search"

        payload = {"question": question}

        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
