'''
# Formulário de Canal
# Este módulo implementa o formulário de canal, permitindo a adição, edição
# e exclusão de canais. Ele utiliza a biblioteca tkinter para a interface
# gráfica, o módulo globals para variáveis globais e o módulo funcoes para
# operações relacionadas ao banco de dados.
'''
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
    '''
    Configura a janela principal do formulário.
    '''
    if g.CANAL_FORM:
        g.CANAL_FORM.destroy()

    g.CANAL_FORM = tk.Toplevel(root)
    g.CANAL_FORM.geometry("340x420")
    g.CANAL_FORM.resizable(False, False)

    icone_path = obter_caminho_icone()
    g.CANAL_FORM.iconbitmap(icone_path)

    no_topo(g.CANAL_FORM)
    posicionar_janela(g.CANAL_FORM, None)

def criar_frame_busca(main_frame):
    '''
    Cria o frame de busca.
    '''
    frame_busca = tk.LabelFrame(main_frame, text='Buscar Canais', pady=5)
    frame_busca.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

    for i in range(3):
        frame_busca.columnconfigure(i, weight=1 if i == 1 else 0)

    tk.Label(frame_busca, text="Valor:").grid(row=0, column=0)
    g.CANAL_BUSCA_ENTRY = tk.Entry(frame_busca)
    g.CANAL_BUSCA_ENTRY.grid(row=0, column=1, sticky="ew")
    g.CANAL_BUSCA_ENTRY.bind("<KeyRelease>", lambda event: buscar('canal'))

    tk.Button(frame_busca, text="Limpar",
              command=lambda: limpar_busca('canal')).grid(row=0, column=2, padx=5, pady=5)

def criar_lista_canais(main_frame):
    '''
    Cria a lista de canais.
    '''
    columns = ("Id", "Canal", "Largura", "Altura", "Compr.", "Obs.")
    g.LIST_CANAL = ttk.Treeview(main_frame, columns=columns, show="headings")
    g.LIST_CANAL["displaycolumns"] = ("Canal", "Largura", "Altura", "Compr.", "Obs.")
    for col in columns:
        g.LIST_CANAL.heading(col, text=col)
        g.LIST_CANAL.column(col, anchor="center", width=20)

    g.LIST_CANAL.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
    listar('canal')

def criar_frame_edicoes(main_frame):
    '''
    Cria o frame de edições.
    '''
    frame_edicoes = configurar_frame_edicoes(main_frame,
                                             text='Novo Canal'
                                             if not g.EDIT_CANAL
                                             else 'Editar Canal'
                                             )

    tk.Label(frame_edicoes, text="Valor:", anchor="w").grid(row=0, column=0, padx=2, sticky='sw')
    g.CANAL_VALOR_ENTRY = tk.Entry(frame_edicoes)
    g.CANAL_VALOR_ENTRY.grid(row=1, column=0, padx=5, sticky="ew")

    tk.Label(frame_edicoes, text="Largura:", anchor="w").grid(row=0, padx=2, column=1, sticky='sw')
    g.CANAL_LARGU_ENTRY = tk.Entry(frame_edicoes)
    g.CANAL_LARGU_ENTRY.grid(row=1, column=1, padx=5, sticky="ew")

    tk.Label(frame_edicoes, text="Altura:", anchor="w").grid(row=2, column=0, padx=2, sticky='sw')
    g.CANAL_ALTUR_ENTRY = tk.Entry(frame_edicoes)
    g.CANAL_ALTUR_ENTRY.grid(row=3, column=0, padx=5, sticky="ew")

    tk.Label(frame_edicoes,
             text="Comprimento total:",
             anchor="w").grid(row=2, column=1, padx=2, sticky='sw')

    g.CANAL_COMPR_ENTRY = tk.Entry(frame_edicoes)
    g.CANAL_COMPR_ENTRY.grid(row=3, column=1, padx=5, sticky="ew")

    tk.Label(frame_edicoes,
             text="Observação:",
             anchor="w").grid(row=4, column=0, padx=2, sticky='sw')

    g.CANAL_OBSER_ENTRY = tk.Entry(frame_edicoes)
    g.CANAL_OBSER_ENTRY.grid(row=5, column=0, columnspan=2, padx=5, sticky="ew")

    return frame_edicoes

def configurar_botoes(main_frame, frame_edicoes):
    '''
    Configura os botões de ação (Adicionar, Atualizar, Excluir).
    '''
    if g.EDIT_CANAL:
        g.CANAL_FORM.title("Editar/Excluir Canal")
        g.LIST_CANAL.bind("<ButtonRelease-1>", lambda event: preencher_campos('canal'))
        frame_edicoes.config(text='Editar Canal')

        tk.Button(main_frame, text="Excluir",
                  command=lambda: excluir('canal'),
                  bg="red").grid(row=2, column=0, padx=5, pady=5, sticky="e")

        tk.Button(frame_edicoes,
                  text="Atualizar",
                  command=lambda: editar('canal'),
                  bg="green").grid(row=1, column=2, padx=5, pady=5, sticky="ew", rowspan=5)
    else:
        g.CANAL_FORM.title("Novo Canal")
        frame_edicoes.config(text='Novo Canal')
        tk.Button(frame_edicoes,
                  text="Adicionar",
                  command=lambda: adicionar('canal'),
                  bg="cyan").grid(row=1, column=2, padx=5, pady=5, sticky="ew", rowspan=5)

def main(root):
    '''
    Inicializa e exibe o formulário de gerenciamento de canais.
    '''
    configurar_janela(root)
    main_frame = configurar_main_frame(g.CANAL_FORM)
    criar_frame_busca(main_frame)
    criar_lista_canais(main_frame)
    frame_edicoes = criar_frame_edicoes(main_frame)
    configurar_botoes(main_frame, frame_edicoes)

if __name__ == "__main__":
    main(None)
