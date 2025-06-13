"""
# Formulário "Sobre"
# Este módulo implementa a janela "Sobre" do aplicativo.
# Ele exibe informações como o nome do aplicativo, versão, autor,
# descrição e um link interativo para o repositório no GitHub.
# A janela é criada como uma Toplevel do Tkinter, centralizada na tela,
# e configurada para permanecer no topo das outras janelas.
# O link para o GitHub abre o navegador padrão ao ser clicado.
"""

import tkinter as tk
import webbrowser
from src import __version__
from src.utils.janelas import no_topo, posicionar_janela
from src.utils.utilitarios import obter_caminho_icone


def main(root, app_principal=None):
    """
    Função principal que cria a janela "Sobre".
    """
    sobre_form = tk.Toplevel(root)
    sobre_form.title("Sobre")
    sobre_form.geometry("300x210")
    sobre_form.resizable(False, False)
    sobre_form.attributes("-topmost", True)  # Define o ícone
    icone_path = obter_caminho_icone()
    sobre_form.iconbitmap(icone_path)

    no_topo(sobre_form, app_principal)
    posicionar_janela(sobre_form, app_principal, "centro")

    label_titulo = tk.Label(sobre_form, text="Cálculo de Dobra", font=("Arial", 16, "bold"))
    label_titulo.pack(pady=10)

    label_versao = tk.Label(sobre_form, text="Versão: 0.1.0-beta", font=("Arial", 12))
    label_versao = tk.Label(sobre_form, text=f"Versão: {__version__}", font=("Arial", 12))
    label_versao.pack(pady=5)

    label_autor = tk.Label(sobre_form, text="Autor: raphadroid27", font=("Arial", 12))
    label_autor.pack(pady=5)

    label_descricao = tk.Label(
        sobre_form, text="Aplicativo para cálculo de dobras.", font=("Arial", 12)
    )
    label_descricao.pack(pady=10)

    def abrir_github():
        webbrowser.open("https://github.com/raphadroid27/Tabela-de-dobra")

    link_github = tk.Label(
        sobre_form,
        text="GitHub: raphadroid27/Tabela-de-dobra",
        font=("Arial", 12),
        fg="blue",
        cursor="hand2",
    )

    link_github.pack(pady=5)
    link_github.bind("<Button-1>", lambda e: abrir_github())


if __name__ == "__main__":
    main(None)
