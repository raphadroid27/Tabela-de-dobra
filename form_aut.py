import tkinter as tk
import globals as g
from models import Usuario
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from funcoes import *


# Configuração do banco de dados
engine = create_engine('sqlite:///tabela_de_dobra.db')
Session = sessionmaker(bind=engine)
session = Session()

def main(root):
    
    if g.AUTEN_FORM is not None:
        g.AUTEN_FORM.destroy()   
        pass

    g.AUTEN_FORM = tk.Toplevel()
    g.AUTEN_FORM.geometry("200x120")
    g.AUTEN_FORM.resizable(False, False)
    g.AUTEN_FORM.attributes('-toolwindow', True)
    g.AUTEN_FORM.attributes("-topmost", True)
    g.AUTEN_FORM.focus()
    desabilitar_janelas()
    g.AUTEN_FORM.protocol("WM_DELETE_WINDOW", lambda: [habilitar_janelas(), g.AUTEN_FORM.destroy()])

    posicionar_janela(g.AUTEN_FORM, 'centro')

    main_frame = tk.Frame(g.AUTEN_FORM)
    main_frame.pack(pady=5, padx=5, fill='both', expand=True)

    main_frame.columnconfigure(0, weight=1)
    main_frame.columnconfigure(1, weight=1)

    main_frame.rowconfigure(0,weight=0)
    main_frame.rowconfigure(1,weight=0)
    main_frame.rowconfigure(2,weight=1)
    main_frame.rowconfigure(3,weight=1)

    tk.Label(main_frame, text="Usuário:").grid(row=0, column=0,padx=5, pady=5)
    g.USUARIO_ENTRY = tk.Entry(main_frame)
    g.USUARIO_ENTRY.focus()
    g.USUARIO_ENTRY.grid(row=0, column=1,padx=5, pady=5)
    tk.Label(main_frame, text="Senha:").grid(row=1, column=0,padx=5, pady=5)
    g.SENHA_ENTRY = tk.Entry(main_frame, show="*")
    g.SENHA_ENTRY.grid(row=1, column=1,padx=5, pady=5)

    admin_existente = session.query(Usuario).filter(Usuario.role == 'admin').first()
    
    if g.LOGIN == True:
        g.AUTEN_FORM.title("Login")
        tk.Button(main_frame, text="Login", command=login).grid(row=3, column=0, columnspan=2,padx=5, pady=5)
    else:
        if not admin_existente:
            g.AUTEN_FORM.geometry("200x150")
            tk.Label(main_frame, text="Admin:").grid(row=2, column=0,padx=5, pady=5)
            g.ADMIN_VAR = 'admin'
            admin_checkbox = tk.Checkbutton(main_frame, variable=g.ADMIN_VAR)
            admin_checkbox.grid(row=2, column=1,padx=5, pady=5)
        else:
             g.ADMIN_VAR = 'viewer'
    
        g.AUTEN_FORM.title("Novo Usuário")
        tk.Button(main_frame, text="Salvar", command=novo_usuario).grid(row=3, column=0, columnspan=2,padx=5, pady=5)

    g.AUTEN_FORM.mainloop()

if __name__ == "__main__":
    main(None)