import tkinter as tk
from tkinter import messagebox
import globals as g
from models import usuario
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import hashlib
from funcoes import *

# Configuração do banco de dados
engine = create_engine('sqlite:///tabela_de_dobra.db')
Session = sessionmaker(bind=engine)
session = Session()
    
def main(root_app):
    g.aut_form = tk.Toplevel()
    g.aut_form.geometry("300x200")
    g.aut_form.resizable(False, False)
    g.aut_form.title("Formulário de Autenticação")
    #g.aut_form.attributes("-topmost", True)

    # Posicionar a janela nova_deducao em relação à janela principal
    g.aut_form.update_idletasks() 
    x = root_app.winfo_x() + ((root_app.winfo_width() - g.aut_form.winfo_width()) // 2)
    y = root_app.winfo_y() + ((root_app.winfo_height() - g.aut_form.winfo_height()) // 2)
    g.aut_form.geometry(f"+{x}+{y}")

    tk.Label(g.aut_form, text="Nome de usuário:").pack(pady=5)
    g.usuario_entry = tk.Entry(g.aut_form)
    g.usuario_entry.pack(pady=5)

    tk.Label(g.aut_form, text="Senha:").pack(pady=5)
    g.senha_entry = tk.Entry(g.aut_form, show="*")
    g.senha_entry.pack(pady=5)

    # Botão de login
    button_login = tk.Button(g.aut_form, text="Login", command=login)
    button_login.pack(pady=20)

    # Iniciar o loop principal da interface gráfica
    g.aut_form.mainloop()

if __name__ == "__main__":
    main(None)