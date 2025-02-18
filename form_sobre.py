import tkinter as tk
import webbrowser
import globals as g
from funcoes import *

def main(root_app):
    g.sobre_form = tk.Toplevel()
    g.sobre_form.title("Sobre")
    g.sobre_form.geometry("300x210")
    g.sobre_form.resizable(False, False)
    g.sobre_form.attributes("-topmost", True)

    janela_centro(g.sobre_form)

    label_titulo = tk.Label(g.sobre_form, text="Tabela de Dobra", font=("Arial", 16, "bold"))
    label_titulo.pack(pady=10)

    label_versao = tk.Label(g.sobre_form, text="Versão: 0.3.8-beta", font=("Arial", 12))
    label_versao.pack(pady=5)

    label_autor = tk.Label(g.sobre_form, text="Autor: raphadroid27", font=("Arial", 12))
    label_autor.pack(pady=5)

    label_descricao = tk.Label(g.sobre_form, text="Aplicativo para cálculo de dobras.", font=("Arial", 12))
    label_descricao.pack(pady=10)

    def abrir_github():
        webbrowser.open("https://github.com/raphadroid27/Tabela-de-dobra")

    link_github = tk.Label(g.sobre_form, text="GitHub: raphadroid27/Tabela-de-dobra", font=("Arial", 12), fg="blue", cursor="hand2")
    link_github.pack(pady=5)
    link_github.bind("<Button-1>", lambda e: abrir_github())

    g.sobre_form.mainloop()

if __name__ == "__main__":
    main(None)