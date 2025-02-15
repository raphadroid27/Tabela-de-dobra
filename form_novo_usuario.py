import tkinter as tk
from tkinter import messagebox
import globals as g
from models import usuario
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Configuração do banco de dados
engine = create_engine('sqlite:///tabela_de_dobra.db')
Session = sessionmaker(bind=engine)
session = Session()

def main(root_app):

    g.novo_usuario_form = tk.Toplevel()
    g.novo_usuario_form.title("Novo Usuário")
    g.novo_usuario_form.geometry("300x200")
    g.novo_usuario_form.resizable(False, False)

    tk.Label(g.novo_usuario_form, text="Nome de usuário:").pack(pady=5)
    novo_usuario_entry = tk.Entry(g.novo_usuario_form)
    novo_usuario_entry.pack(pady=5)
    tk.Label(g.novo_usuario_form, text="Senha:").pack(pady=5)
    novo_senha_entry = tk.Entry(g.novo_usuario_form, show="*")
    novo_senha_entry.pack(pady=5)

    def salvar_usuario():
        nome_usuario = novo_usuario_entry.get()
        senha_usuario = novo_senha_entry.get()
        if nome_usuario == "" or senha_usuario == "":
            messagebox.showerror("Erro", "Preencha todos os campos.")
            return
        
        usuario_existente = session.query(usuario).filter_by(nome=nome_usuario).first()
        if usuario_existente:
            messagebox.showerror("Erro", "Usuário já existente.")
            return
        else:
            novo_usuario = usuario(nome=nome_usuario, senha=senha_usuario)
            session.add(novo_usuario)
            session.commit()
            messagebox.showinfo("Sucesso", "Usuário cadastrado com sucesso.")
            g.novo_usuario_form.destroy()


    tk.Button(g.novo_usuario_form, text="Salvar", command=salvar_usuario).pack(pady=20)

    g.novo_usuario_form.mainloop()

if __name__ == "__main__":
    main(None)