import tkinter as tk
from tkinter import messagebox
import globals as g
from models import usuario  # Certifique-se de importar a classe correta
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import hashlib

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
    novo_usuario_entry = tk.Entry(g.novo_usuario_form)
    novo_usuario_entry.pack(pady=5)
    tk.Label(g.novo_usuario_form, text="Senha:").pack(pady=5)
    novo_senha_entry = tk.Entry(g.novo_usuario_form, show="*")
    novo_senha_entry.pack(pady=5)

    admin_existente = session.query(usuario).filter(usuario.admin == True).first()
    if not admin_existente:
        tk.Label(g.novo_usuario_form, text="Admin:").pack(pady=5)
        admin_var = tk.IntVar()
        admin_checkbox = tk.Checkbutton(g.novo_usuario_form, variable=admin_var)
        admin_checkbox.pack(pady=5)
    else:
        admin_var = tk.IntVar(value=0)

    def salvar_usuario():
        novo_usuario_nome = novo_usuario_entry.get()
        novo_usuario_senha = novo_senha_entry.get()
        senha_hash = hashlib.sha256(novo_usuario_senha.encode()).hexdigest()
        if novo_usuario_nome == "" or novo_usuario_senha == "":
            messagebox.showerror("Erro", "Preencha todos os campos.")
            return
        
        usuario_obj = session.query(usuario).filter_by(nome=novo_usuario_nome).first()
        if usuario_obj:
            messagebox.showerror("Erro", "Usuário já existente.")
            return
        else:
            novo_usuario = usuario(nome=novo_usuario_nome, senha=senha_hash, admin=admin_var.get())
            session.add(novo_usuario)
            session.commit()
            messagebox.showinfo("Sucesso", "Usuário cadastrado com sucesso.")
            g.novo_usuario_form.destroy()

    tk.Button(g.novo_usuario_form, text="Salvar", command=salvar_usuario).pack(pady=20)

    g.novo_usuario_form.mainloop()

if __name__ == "__main__":
    main(None)