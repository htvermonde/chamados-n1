from pathlib import Path
import os

try:
    from dotenv import load_dotenv

    root = Path(__file__).resolve().parent
    env_path = root / ".env"
    print(f"Buscando .env em: {env_path}")
    print(f"Arquivo existe? {env_path.exists()}")
    success = load_dotenv(dotenv_path=env_path, override=True)
    print(f"Sucesso no load_dotenv: {success}")
    print(f"N1_OPENAI_API_KEY existe? {bool(os.environ.get('N1_OPENAI_API_KEY'))}")
except ImportError:
    print("python-dotenv não está instalado")
except Exception as e:
    print(f"Erro: {e}")
