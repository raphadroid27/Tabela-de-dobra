import tkinter as tk
import globals as g
from models import usuario
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from funcoes import *


# Configuração do banco de dados
engine = create_engine('sqlite:///tabela_de_dobra.db')
Session = sessionmaker(bind=engine)
session = Session()

def main(root_app):
    
    if g.aut_form is not None:
        g.aut_form.destroy()   
        pass

    g.aut_form = tk.Toplevel()
    g.aut_form.geometry("200x120")
    g.aut_form.resizable(False, False)
    g.aut_form.attributes('-toolwindow', True)
    g.aut_form.attributes("-topmost", True)
    g.aut_form.focus()
    desabilitar_janelas()
    g.aut_form.protocol("WM_DELETE_WINDOW", lambda: [habilitar_janelas(), g.aut_form.destroy()])

    janela_centro(g.aut_form)

    main_frame = tk.Frame(g.aut_form)
    main_frame.pack(pady=5, padx=5, fill='both', expand=True)

    main_frame.columnconfigure(0, weight=1)
    main_frame.columnconfigure(1, weight=1)

    main_frame.rowconfigure(0,weight=0)
    main_frame.rowconfigure(1,weight=0)
    main_frame.rowconfigure(2,weight=1)
    main_frame.rowconfigure(3,weight=1)

    tk.Label(main_frame, text="Usuário:").grid(row=0, column=0,padx=5, pady=5)
    g.usuario_entry = tk.Entry(main_frame)
    g.usuario_entry.focus()
    g.usuario_entry.grid(row=0, column=1,padx=5, pady=5)
    tk.Label(main_frame, text="Senha:").grid(row=1, column=0,padx=5, pady=5)
    g.senha_entry = tk.Entry(main_frame, show="*")
    g.senha_entry.grid(row=1, column=1,padx=5, pady=5)

    admin_existente = session.query(usuario).filter(usuario.admin == True).first()
    
    if g.login == True:
        g.aut_form.title("Login")
        tk.Button(main_frame, text="Login", command=login).grid(row=3, column=0, columnspan=2,padx=5, pady=5)
    else:
        if not admin_existente:
            g.aut_form.geometry("200x150")
            tk.Label(main_frame, text="Admin:").grid(row=2, column=0,padx=5, pady=5)
            g.admin_var = tk.IntVar()
            admin_checkbox = tk.Checkbutton(main_frame, variable=g.admin_var)
            admin_checkbox.grid(row=2, column=1,padx=5, pady=5)
        else:
            g.admin_var = tk.IntVar(value=0)
    
        g.aut_form.title("Novo Usuário")
        tk.Button(main_frame, text="Salvar", command=novo_usuario).grid(row=3, column=0, columnspan=2,padx=5, pady=5)

    g.aut_form.mainloop()

if __name__ == "__main__":
    main(None)