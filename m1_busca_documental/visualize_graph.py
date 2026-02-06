import sys
from pathlib import Path

# Garante que a raiz do projeto está no path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from m1_busca_documental.graph import rag_graph


def visualize():
    try:
        # Tenta gerar a representação ASCII
        print("\n--- Representação ASCII do Grafo ---\n")
        rag_graph.get_graph().print_ascii()

        # Tenta salvar como PNG usando Mermaid (requer conexão ou dependências)
        output_path = _PROJECT_ROOT / "graph_visualization.png"
        print(f"\nTentando gerar imagem em: {output_path}")

        # O método draw_mermaid_png costuma usar uma API externa (mermaid.ink)
        # por padrão se não houver dependências locais.
        png_data = rag_graph.get_graph().draw_mermaid_png()
        with open(output_path, "wb") as f:
            f.write(png_data)

        print(f"Sucesso! Imagem salva em: {output_path}")

    except Exception as e:
        print(f"\nErro ao gerar imagem: {e}")
        print(
            "Dica: Certifique-se de ter as extensões de visualização do LangGraph instaladas."
        )

    try:
        # Tenta gerar o código Mermaid (Markdown)
        print("\n--- Código Mermaid (Copie e cole em mermaid.live) ---\n")
        mermaid_code = rag_graph.get_graph().draw_mermaid()
        print(mermaid_code)

    except Exception as e:
        print(f"\nErro ao gerar Mermaid: {e}")


if __name__ == "__main__":
    visualize()
