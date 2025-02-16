import tkinter as tk
from tkinter import messagebox
import globals as g
from models import usuario  # Certifique-se de importar a classe correta
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from funcoes import *

# Configuração do banco de dados
engine = create_engine('sqlite:///tabela_de_dobra.db')
Session = sessionmaker(bind=engine)
session = Session()

def main(root_app):

    g.novo_usuario_form = tk.Tk()
    g.novo_usuario_form.title("Novo Usuário")
    g.novo_usuario_form.geometry("300x300")
    g.novo_usuario_form.resizable(False, False)

    tk.Label(g.novo_usuario_form, text="Nome de usuário:").pack(pady=5)
    g.novo_usuario_entry = tk.Entry(g.novo_usuario_form)
    g.novo_usuario_entry.pack(pady=5)
    tk.Label(g.novo_usuario_form, text="Senha:").pack(pady=5)
    g.novo_senha_entry = tk.Entry(g.novo_usuario_form, show="*")
    g.novo_senha_entry.pack(pady=5)

    admin_existente = session.query(usuario).filter(usuario.admin == True).first()
    if not admin_existente:
        tk.Label(g.novo_usuario_form, text="Admin:").pack(pady=5)
        g.admin_var = tk.IntVar()
        admin_checkbox = tk.Checkbutton(g.novo_usuario_form, variable=g.admin_var)
        admin_checkbox.pack(pady=5)
    else:
        g.admin_var = tk.IntVar(value=0)

    tk.Button(g.novo_usuario_form, text="Salvar", command=novo_usuario).pack(pady=20)

    g.novo_usuario_form.mainloop()

if __name__ == "__main__":
    main(None)