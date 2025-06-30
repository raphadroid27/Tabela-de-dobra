"""
# Formulário de Material
# Este módulo contém a implementação do formulário de materiais, que permite
# adicionar, editar e excluir materiais. O formulário é
# construído usando a biblioteca tkinter e utiliza o módulo globals para
# armazenar variáveis globais e o módulo funcoes para realizar operações
# relacionadas ao banco de dados.
"""
import tkinter as tk
from tkinter import ttk
from src.utils.janelas import (no_topo, posicionar_janela)
from src.utils.interface import (listar,
                                 limpar_busca,
                                 configurar_main_frame,
                                 configurar_frame_edicoes
                                 )
from src.utils.utilitarios import obter_caminho_icone
from src.utils.operacoes_crud import (buscar,
                                      preencher_campos,
                                      excluir,
                                      editar,
                                      adicionar
                                      )
from src.config import globals as g


def configurar_janela(root):
    """
    Configura a janela principal do formulário de materiais.
    """
    if g.MATER_FORM:
        g.MATER_FORM.destroy()

    g.MATER_FORM = tk.Toplevel(root)
    g.MATER_FORM.geometry("340x420")
    g.MATER_FORM.resizable(False, False)

    icone_path = obter_caminho_icone()
    g.MATER_FORM.iconbitmap(icone_path)

    no_topo(g.MATER_FORM)
    posicionar_janela(g.MATER_FORM, None)


def criar_frame_busca(main_frame):
    """
    Cria o frame de busca.
    """
    frame_busca = tk.LabelFrame(main_frame, text='Buscar Materiais', pady=5)
    frame_busca.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

    for i in range(3):
        frame_busca.columnconfigure(i, weight=1 if i == 1 else 0)

    tk.Label(frame_busca, text="Nome:").grid(row=0, column=0)
    g.MAT_BUSCA_ENTRY = tk.Entry(frame_busca)
    g.MAT_BUSCA_ENTRY.grid(row=0, column=1, sticky="ew")
    g.MAT_BUSCA_ENTRY.bind("<KeyRelease>", lambda event: buscar('material'))

    tk.Button(frame_busca,
              text="Limpar",
              bg='lightyellow',
              command=lambda: limpar_busca('material')).grid(row=0, column=2, padx=5, pady=5)


def criar_lista_materiais(main_frame):
    """
    Cria a lista de materiais.
    """
    columns = ("Id", "Nome", "Densidade", "Escoamento", "Elasticidade")
    g.LIST_MAT = ttk.Treeview(main_frame, columns=columns, show="headings")
    g.LIST_MAT["displaycolumns"] = ("Nome", "Densidade", "Escoamento", "Elasticidade")
    for col in columns:
        g.LIST_MAT.heading(col, text=col)
        g.LIST_MAT.column(col, anchor="center", width=20)

    g.LIST_MAT.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
    listar('material')


def criar_frame_edicoes(main_frame):
    """
    Cria o frame de edições.
    """
    frame_edicoes = configurar_frame_edicoes(main_frame,
                                             text='Novo Material'
                                             if not g.EDIT_MAT
                                             else 'Editar Material',
                                             )

    tk.Label(frame_edicoes, text="Nome:", anchor="w").grid(row=0, column=0, padx=2, sticky='sw')
    g.MAT_NOME_ENTRY = tk.Entry(frame_edicoes)
    g.MAT_NOME_ENTRY.grid(row=1, column=0, padx=5, sticky="ew")

    tk.Label(frame_edicoes, text="Densidade:", anchor="w").grid(row=0,
                                                                column=1,
                                                                padx=2,
                                                                sticky='sw'
                                                                )
    g.MAT_DENS_ENTRY = tk.Entry(frame_edicoes)
    g.MAT_DENS_ENTRY.grid(row=1, column=1, padx=5, sticky="ew")

    tk.Label(frame_edicoes, text="Escoamento:", anchor="w").grid(row=2,
                                                                 column=0,
                                                                 padx=2,
                                                                 sticky='sw'
                                                                 )
    g.MAT_ESCO_ENTRY = tk.Entry(frame_edicoes)
    g.MAT_ESCO_ENTRY.grid(row=3, column=0, padx=5, sticky="ew")

    tk.Label(frame_edicoes, text="Elasticidade:", anchor="w").grid(row=2,
                                                                   column=1,
                                                                   padx=2,
                                                                   sticky='sw'
                                                                   )
    g.MAT_ELAS_ENTRY = tk.Entry(frame_edicoes)
    g.MAT_ELAS_ENTRY.grid(row=3, column=1, padx=5, sticky="ew")

    return frame_edicoes


def configurar_botoes(main_frame, frame_edicoes):
    """
    Configura os botões de ação (Adicionar, Atualizar, Excluir).
    """
    if g.MATER_FORM is not None:
        if g.EDIT_MAT:
            g.MATER_FORM.title("Editar/Excluir Material")
            if g.LIST_MAT is not None:
                g.LIST_MAT.bind("<ButtonRelease-1>", lambda event: preencher_campos('material'))
            else:
                print("Erro: g.LIST_MAT não foi inicializado.")
            frame_edicoes.config(text='Editar Material')

            tk.Button(main_frame,
                      text="Excluir",
                      command=lambda: excluir('material'),
                      bg="lightcoral").grid(row=2, column=0, padx=5, pady=5, sticky="e")

            tk.Button(frame_edicoes,
                      text="Atualizar",
                      command=lambda: editar('material'),
                      bg="lightgreen").grid(row=1, column=2, padx=5, pady=5, sticky="ew", rowspan=3)
        else:
            g.MATER_FORM.title("Adicionar Material")
            frame_edicoes.config(text='Novo Material')
            tk.Button(frame_edicoes,
                      text="Adicionar",
                      command=lambda: adicionar('material'),
                      bg="lightblue").grid(row=1, column=2, padx=5, pady=5, sticky="ew", rowspan=3)
    else:
        print("Erro: g.MATER_FORM não foi inicializado.")


def main(root):
    """
    Inicializa e exibe o formulário de gerenciamento de materiais.
    """
    configurar_janela(root)
    main_frame = configurar_main_frame(g.MATER_FORM)
    criar_frame_busca(main_frame)
    criar_lista_materiais(main_frame)
    frame_edicoes = criar_frame_edicoes(main_frame)
    configurar_botoes(main_frame, frame_edicoes)


if __name__ == "__main__":
    main(None)
