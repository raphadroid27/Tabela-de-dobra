'''
# Formulário de Gerenciamento de Usuários
# Este módulo implementa uma interface gráfica para gerenciar usuários do sistema.
# As funcionalidades incluem redefinir senhas, alterar permissões e excluir usuários.
# A interface é construída com a biblioteca tkinter, utilizando o módulo globals
# para variáveis globais e o módulo funcoes para operações relacionadas ao banco de dados.
'''
import tkinter as tk
from tkinter import ttk
from funcoes import (tem_permissao,
                     no_topo, posicionar_janela,
                     buscar, limpar_busca, listar,
                     resetar_senha,
                     excluir_usuario,
                     tornar_editor)
import globals as g

def main(root):
    """
    Função principal para gerenciar usuários.
    Inicializa a interface gráfica para edição, exclusão e gerenciamento de permissões.
    """
    # Verificar se o usuário é administrador
    if not tem_permissao('admin'):
        return

    if g.USUAR_FORM is not None:
        g.USUAR_FORM.destroy()

    g.USUAR_FORM = tk.Toplevel(root)
    g.USUAR_FORM.title("Editar/Excluir Usuário")
    g.USUAR_FORM.geometry("300x280")
    g.USUAR_FORM.resizable(False, False)

    no_topo(g.USUAR_FORM)
    posicionar_janela(g.USUAR_FORM, 'centro')

    main_frame = tk.Frame(g.USUAR_FORM)
    main_frame.pack(pady=5, padx=5, fill='both', expand=True)

    for i in range(3):
        main_frame.columnconfigure(i, weight=1)

    for i in range(3):
        main_frame.rowconfigure(i, weight=1 if i == 1 else 0)

    frame_busca = tk.LabelFrame(main_frame, text='Filtrar Usuários', pady=5)
    frame_busca.grid(row=0, column=0, padx=5, pady=5, sticky="ew", columnspan=3)

    for i in range(3):
        frame_busca.columnconfigure(i, weight=1 if i == 1 else 0)

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
        g.LIST_USUARIO.column(col, anchor="center", width=20)

    g.LIST_USUARIO.grid(row=1, column=0, padx=5, pady=5, sticky="ew", columnspan=3)

    tk.Button(main_frame,
             text="Tornar Editor",
             command=tornar_editor,
             bg="green",
             width=10).grid(row=2, column=0, padx=5, pady=5, sticky="w")

    tk.Button(main_frame,
              text="Resetar Senha",
              command=resetar_senha,
              bg="yellow",
              width=10).grid(row=2, column=1, padx=5, pady=5, sticky="ew")

    tk.Button(main_frame,
              text="Excluir",
              command=excluir_usuario,
              bg="red",
              width=10).grid(row=2, column=2, padx=5, pady=5, sticky="e")

    listar('usuario')

    g.USUAR_FORM.mainloop()

if __name__ == "__main__":
    main(None)
