import tkinter as tk
from tkinter import ttk
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from funcoes import *

# Configuração do banco de dados
engine = create_engine('sqlite:///tabela_de_dobra.db')
Session = sessionmaker(bind=engine)
session = Session()

def main(root_app):
    # Verificar se o usuário é administrador
    if not admin('usuario'):
        return

    if g.usuario_form is not None:
        g.usuario_form.destroy()   
        pass

    g.usuario_form = tk.Toplevel()
    g.usuario_form.title("Editar/Excluir Usuário")
    g.usuario_form.geometry("340x280")
    g.usuario_form.resizable(False, False)

    on_top(g.usuario_form)
    janela_direita(g.usuario_form)

    main_frame = tk.Frame(g.usuario_form)
    main_frame.pack(pady=5, padx=5, fill='both', expand=True)

    main_frame.columnconfigure(0,weight=1)

    main_frame.rowconfigure(0,weight=0)
    main_frame.rowconfigure(1,weight=1)
    main_frame.rowconfigure(2,weight=0)
    main_frame.rowconfigure(3,weight=0)

    frame_busca = tk.LabelFrame(main_frame, text='Filtrar Usuários', pady=5)
    frame_busca.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

    frame_busca.columnconfigure(0, weight=0)
    frame_busca.columnconfigure(1, weight=1)
    frame_busca.columnconfigure(2, weight=0)

    tk.Label(frame_busca, text="Usuário:").grid(row=0,column=0)
    g.usuario_valor_entry=tk.Entry(frame_busca)
    g.usuario_valor_entry.grid(row=0, column=1, sticky="ew")
    g.usuario_valor_entry.bind("<KeyRelease>", lambda event: buscar('usuario'))

    tk.Button(frame_busca, text="Limpar", command = lambda: limpar_busca('usuario')).grid(row=0, column=2, padx=5, pady=5)

    columns = ("Id","Nome")
    g.lista_usuario = ttk.Treeview(main_frame, columns=columns, show="headings")
    for col in columns:
        g.lista_usuario["displaycolumns"] = ("Nome")
        g.lista_usuario.heading(col, text=col)
        g.lista_usuario.column(col, anchor="center")    
    
    g.lista_usuario.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        
    tk.Button(main_frame, text="Excluir", command=excluir_usuario, bg="red").grid(row=2, column=0, padx=5, pady=5, sticky="e")

    listar('usuario')

    g.usuario_form.mainloop()

if __name__ == "__main__":
    main(None)
