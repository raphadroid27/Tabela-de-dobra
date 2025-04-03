import tkinter as tk
import webbrowser
import globals as g
from funcoes import *

def main(root):
    g.SOBRE_FORM = tk.Toplevel()
    g.SOBRE_FORM.title("Sobre")
    g.SOBRE_FORM.geometry("300x210")
    g.SOBRE_FORM.resizable(False, False)
    g.SOBRE_FORM.attributes("-topmost", True)

    no_topo(g.SOBRE_FORM)
    posicionar_janela(g.SOBRE_FORM, 'centro')
    
    label_titulo = tk.Label(g.SOBRE_FORM, text="Tabela de Dobra", font=("Arial", 16, "bold"))
    label_titulo.pack(pady=10)

    label_versao = tk.Label(g.sobre_form, text="Versão: 0.1.0-beta", font=("Arial", 12))
    label_versao.pack(pady=5)

    label_autor = tk.Label(g.SOBRE_FORM, text="Autor: raphadroid27", font=("Arial", 12))
    label_autor.pack(pady=5)

    label_descricao = tk.Label(g.SOBRE_FORM, text="Aplicativo para cálculo de dobras.", font=("Arial", 12))
    label_descricao.pack(pady=10)

    def abrir_github():
        webbrowser.open("https://github.com/raphadroid27/Tabela-de-dobra")

    link_github = tk.Label(g.SOBRE_FORM, text="GitHub: raphadroid27/Tabela-de-dobra", font=("Arial", 12), fg="blue", cursor="hand2")
    link_github.pack(pady=5)
    link_github.bind("<Button-1>", lambda e: abrir_github())

    g.SOBRE_FORM.mainloop()

if __name__ == "__main__":
    main(None)