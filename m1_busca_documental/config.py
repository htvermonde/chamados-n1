# m1_busca_documental/config.py
"""Configurações do M1 — Motor de Busca Documental. Lê variáveis do .env na raiz do projeto."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Raiz do projeto (onde está o .env principal)
ROOT_DIR = Path(__file__).resolve().parent.parent
env_path = ROOT_DIR / ".env"

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv(dotenv_path=env_path)


def _env(key: str, default: str = "") -> str:
    """Helper para ler variáveis de ambiente."""
    return os.environ.get(key, default) or default


# --- Configurações Extraídas ---

# Documentos locais
DOCS_REPO_PATH = _env("M1_DOCS_REPO") or str(ROOT_DIR / "documento_busca")

# API LibIndexr
LIBINDEXR_BASE_URL = _env(
    "LIBINDEXR_BASE_URL", "https://libindexr.dev.saiapplications.com"
)
LIBINDEXR_API_KEY = _env("LIBINDEXR_API_KEY")
INDEX_ID = _env("M1_INDEX_ID")

# Parâmetros de Busca
DEFAULT_QUANTITY = 3
DEFAULT_THRESHOLD_SIMILARITY = 0.4

# OpenAI 
OPENAI_API_KEY = _env("N1_OPENAI_API_KEY_AF")
LLM_MODEL = _env("M1_LLM_MODEL", "gpt-4o")
