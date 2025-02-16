import tkinter as tk
from tkinter import messagebox
import globals as g
from models import usuario
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import hashlib

# Configuração do banco de dados
engine = create_engine('sqlite:///tabela_de_dobra.db')
Session = sessionmaker(bind=engine)
session = Session()

def autenticacao():
    usuario_nome = usuario_entry.get()
    usuario_senha = senha_entry.get()
    
    usuario_obj = session.query(usuario).filter_by(nome=usuario_nome).first()

    if usuario_obj and usuario_obj.senha == hashlib.sha256(usuario_senha.encode()).hexdigest():
        messagebox.showinfo("Login", "Login efetuado com sucesso.")
        g.aut_form.destroy()
    else:
        messagebox.showerror("Erro", "Usuário ou senha incorretos.")
    
# Configuração da janela principal
g.aut_form = tk.Tk()
g.aut_form.geometry("300x200")
g.aut_form.resizable(False, False)
g.aut_form.title("Formulário de Autenticação")

# Rótulos e campos de entrada
tk.Label(g.aut_form, text="Nome de usuário:").pack(pady=5)
usuario_entry = tk.Entry(g.aut_form)
usuario_entry.pack(pady=5)

tk.Label(g.aut_form, text="Senha:").pack(pady=5)
senha_entry = tk.Entry(g.aut_form, show="*")
senha_entry.pack(pady=5)

# Botão de login
button_login = tk.Button(g.aut_form, text="Login", command=autenticacao)
button_login.pack(pady=20)

# Iniciar o loop principal da interface gráfica
g.aut_form.mainloop()