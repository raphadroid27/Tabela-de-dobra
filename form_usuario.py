'''
Módulo para criar a janela de edição/exclusão de usuários.
Este módulo contém a função principal que cria a interface gráfica
para editar e excluir usuários do sistema.
Ele também inclui funções para buscar, limpar a busca,
listar usuários, resetar senhas, excluir usuários e tornar usuários editores.
'''

import tkinter as tk
from tkinter import ttk
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from funcoes import (tem_permissao,
                     no_topo, posicionar_janela,
                     buscar, limpar_busca, listar,
                     resetar_senha,
                     excluir_usuario,
                     tornar_editor)
import globals as g

# Configuração do banco de dados
engine = create_engine('sqlite:///tabela_de_dobra.db')
Session = sessionmaker(bind=engine)
session = Session()

def main(root_app):
    '''
    Função principal para gerenciar usuários.
    '''
    # Verificar se o usuário é administrador
    if not tem_permissao('admin'):
        return

    if g.USUAR_FORM is not None:
        g.USUAR_FORM.destroy()

    g.USUAR_FORM = tk.Toplevel(root_app)
    g.USUAR_FORM.title("Editar/Excluir Usuário")
    g.USUAR_FORM.geometry("300x280")
    g.USUAR_FORM.resizable(False, False)

    no_topo(g.USUAR_FORM)
    posicionar_janela(g.USUAR_FORM, 'centro')

    main_frame = tk.Frame(g.USUAR_FORM)
    main_frame.pack(pady=5, padx=5, fill='both', expand=True)

    main_frame.columnconfigure(0,weight=1)

    main_frame.rowconfigure(0,weight=0)
    main_frame.rowconfigure(1,weight=1)
    main_frame.rowconfigure(2,weight=0)
    main_frame.rowconfigure(3,weight=0)

    frame_busca = tk.LabelFrame(main_frame, text='Filtrar Usuários', pady=5)
    frame_busca.grid(row=0, column=0, padx=5, pady=5, sticky="ew", columnspan=2)

    frame_busca.columnconfigure(0, weight=0)
    frame_busca.columnconfigure(1, weight=1)
    frame_busca.columnconfigure(2, weight=0)

    tk.Label(frame_busca, text="Usuário:").grid(row=0,column=0)
    g.USUARIO_BUSCA_ENTRY=tk.Entry(frame_busca)
    g.USUARIO_BUSCA_ENTRY.grid(row=0, column=1, sticky="ew")
    g.USUARIO_BUSCA_ENTRY.bind("<KeyRelease>", lambda event: buscar('usuario'))

    tk.Button(frame_busca,
              text="Limpar",
              command = lambda: limpar_busca('usuario')).grid(row=0, column=2, padx=5, pady=5)

    columns = ("Id","Nome", "Permissões")
    g.LIST_USUARIO = ttk.Treeview(main_frame, columns=columns, show="headings")
    for col in columns:
        g.LIST_USUARIO["displaycolumns"] = ("Nome", "Permissões")
        g.LIST_USUARIO.heading(col, text=col)
        g.LIST_USUARIO.column(col, anchor="center")

    g.LIST_USUARIO.grid(row=1, column=0, padx=5, pady=5, sticky="ew", columnspan=2)

    tk.Button(main_frame,
              text="Resetar Senha",
              command=resetar_senha,
              bg="yellow").grid(row=2, column=0, padx=5, pady=5, sticky="e")

    tk.Button(main_frame,
              text="Excluir",
              command=excluir_usuario,
              bg="red").grid(row=2, column=1, padx=5, pady=5, sticky="e")

    tk.Button(main_frame,
              text="Tornar Editor",
              command=tornar_editor,
              bg="green").grid(row=3, column=0, padx=5, pady=5, sticky="e")

    listar('usuario')

    g.USUAR_FORM.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    main(root)
