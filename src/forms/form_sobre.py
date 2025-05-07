'''
# Formulário "Sobre"
# Este módulo implementa a janela "Sobre" do aplicativo.
# Ele exibe informações como o nome do aplicativo, versão, autor,
# descrição e um link interativo para o repositório no GitHub.
# A janela é criada como uma Toplevel do Tkinter, centralizada na tela,
# e configurada para permanecer no topo das outras janelas.
# O link para o GitHub abre o navegador padrão ao ser clicado.
'''
import tkinter as tk
import webbrowser
from src import __version__
from src.config import globals as g
from src.utils.janelas import (no_topo, posicionar_janela)
from src.utils.utilitarios import obter_caminho_icone

def main(root):
    '''
    Função principal que cria a janela "Sobre".
    '''
    g.SOBRE_FORM = tk.Toplevel(root)
    g.SOBRE_FORM.title("Sobre")
    g.SOBRE_FORM.geometry("300x210")
    g.SOBRE_FORM.resizable(False, False)
    g.SOBRE_FORM.attributes("-topmost", True)

    # Define o ícone
    icone_path = obter_caminho_icone()
    g.SOBRE_FORM.iconbitmap(icone_path)

    no_topo(g.SOBRE_FORM)
    posicionar_janela(g.SOBRE_FORM, 'centro')

    label_titulo = tk.Label(g.SOBRE_FORM, text="Cálculo de Dobra", font=("Arial", 16, "bold"))
    label_titulo.pack(pady=10)

    label_versao = tk.Label(g.SOBRE_FORM, text="Versão: 0.1.0-beta", font=("Arial", 12))
    label_versao = tk.Label(g.SOBRE_FORM, text=f"Versão: {__version__}", font=("Arial", 12))
    label_versao.pack(pady=5)

    label_autor = tk.Label(g.SOBRE_FORM, text="Autor: raphadroid27", font=("Arial", 12))
    label_autor.pack(pady=5)

    label_descricao = tk.Label(g.SOBRE_FORM,
                               text="Aplicativo para cálculo de dobras.",
                               font=("Arial", 12))
    label_descricao.pack(pady=10)

    def abrir_github():
        webbrowser.open("https://github.com/raphadroid27/Tabela-de-dobra")

    link_github = tk.Label(g.SOBRE_FORM,
                           text="GitHub: raphadroid27/Tabela-de-dobra",
                           font=("Arial", 12),
                           fg="blue",
                           cursor="hand2")

    link_github.pack(pady=5)
    link_github.bind("<Button-1>", lambda e: abrir_github())

if __name__ == "__main__":
    main(None)
