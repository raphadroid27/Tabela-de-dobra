'''
# Formulário de Dedução
# Este módulo implementa o formulário de dedução, permitindo a adição, edição
# e exclusão de deduções. Ele utiliza a biblioteca tkinter para a interface
# gráfica, o módulo globals para variáveis globais e o módulo funcoes para
# operações relacionadas ao banco de dados.
'''
import tkinter as tk
from tkinter import ttk
from src.utils.janelas import (no_topo, posicionar_janela)
from src.utils.interface import (listar,
                                 limpar_busca,
                                 atualizar_widgets,
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
    Configura a janela principal do formulário de deduções.
    '''
    if g.DEDUC_FORM:
        g.DEDUC_FORM.destroy()

    g.DEDUC_FORM = tk.Toplevel(root)
    g.DEDUC_FORM.geometry("500x420")
    g.DEDUC_FORM.resizable(False, False)

    icone_path = obter_caminho_icone()
    g.DEDUC_FORM.iconbitmap(icone_path)

    no_topo(g.DEDUC_FORM)
    posicionar_janela(g.DEDUC_FORM, None)

def criar_frame_busca(main_frame):
    '''
    Cria o frame de busca.
    '''
    frame_busca = tk.LabelFrame(main_frame, text='Buscar Deduções', pady=5)
    frame_busca.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

    for i in range(4):
        frame_busca.columnconfigure(i, weight=1)

    tk.Label(frame_busca, text="Material:").grid(row=0, column=0, padx=2, sticky='sw')
    g.DED_MATER_COMB = ttk.Combobox(frame_busca)
    g.DED_MATER_COMB.grid(row=1, column=0, padx=5, sticky="ew")
    g.DED_MATER_COMB.bind("<<ComboboxSelected>>", lambda event: buscar('dedução'))

    tk.Label(frame_busca, text="Espessura:").grid(row=0, column=1, padx=2, sticky='sw')
    g.DED_ESPES_COMB = ttk.Combobox(frame_busca)
    g.DED_ESPES_COMB.grid(row=1, column=1, padx=5, sticky="ew")
    g.DED_ESPES_COMB.bind("<<ComboboxSelected>>", lambda event: buscar('dedução'))

    tk.Label(frame_busca, text="Canal:").grid(row=0, column=2, padx=2, sticky='sw')
    g.DED_CANAL_COMB = ttk.Combobox(frame_busca)
    g.DED_CANAL_COMB.grid(row=1, column=2, padx=5, sticky="ew")
    g.DED_CANAL_COMB.bind("<<ComboboxSelected>>", lambda event: buscar('dedução'))

    tk.Button(frame_busca,
              text="Limpar",
              width=10,
              command=lambda: limpar_busca('dedução')).grid(row=1, column=3, padx=5, pady=5)

def criar_lista_deducoes(main_frame):
    '''
    Cria a lista de deduções.
    '''
    columns = ("Id", "Material", "Espessura", "Canal", "Dedução", "Observação", "Força")
    g.LIST_DED = ttk.Treeview(main_frame, columns=columns, show="headings")
    g.LIST_DED["displaycolumns"] = ("Material",
                                    "Espessura",
                                    "Canal",
                                    "Dedução",
                                    "Observação",
                                    "Força"
                                    )
    for col in columns:
        g.LIST_DED.heading(col, text=col)
        g.LIST_DED.column(col, anchor="center", width=60)
        g.LIST_DED.column("Material", width=80)
        g.LIST_DED.column("Observação", width=120, anchor="w")

    g.LIST_DED.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
    listar('dedução')

def criar_frame_edicoes(main_frame):
    '''
    Cria o frame de edições.
    '''
    frame_edicoes = configurar_frame_edicoes(main_frame,
                                             text='Nova Dedução'
                                             if not g.EDIT_DED
                                             else 'Editar Dedução'
                                             )

    tk.Label(frame_edicoes, text="Valor:").grid(row=0, column=0, padx=2, sticky='sw')
    g.DED_VALOR_ENTRY = tk.Entry(frame_edicoes)
    g.DED_VALOR_ENTRY.grid(row=1, column=0, padx=5, sticky="ew")

    tk.Label(frame_edicoes, text="Observação:").grid(row=0, column=1, padx=2, sticky='sw')
    g.DED_OBSER_ENTRY = tk.Entry(frame_edicoes)
    g.DED_OBSER_ENTRY.grid(row=1, column=1, padx=5, sticky="ew")

    tk.Label(frame_edicoes, text="Força:").grid(row=0, column=2, padx=2, sticky='sw')
    g.DED_FORCA_ENTRY = tk.Entry(frame_edicoes)
    g.DED_FORCA_ENTRY.grid(row=1, column=2, padx=5, sticky="ew")

    return frame_edicoes

def configurar_botoes(main_frame, frame_edicoes):
    '''
    Configura os botões de ação (Adicionar, Atualizar, Excluir).
    '''
    if g.EDIT_DED:
        g.DEDUC_FORM.title("Editar/Excluir Dedução")
        g.LIST_DED.bind("<ButtonRelease-1>", lambda event: preencher_campos('dedução'))
        frame_edicoes.config(text='Editar Dedução')

        tk.Button(frame_edicoes,
                  text="Atualizar",
                  bg="green",
                  width=10,
                  command=lambda: editar('dedução')).grid(row=1,
                                                          column=3,
                                                          padx=5,
                                                          pady=5,
                                                          sticky="eW"
                                                          )
        tk.Button(main_frame,
                  text="Excluir",
                  bg="red",
                  width=10,
                  command=lambda: excluir('dedução')).grid(row=2,
                                                           column=0,
                                                           padx=5,
                                                           pady=5,
                                                           sticky="e"
                                                           )
    else:
        g.DEDUC_FORM.title("Adicionar Dedução")
        frame_edicoes.config(text='Nova Dedução')
        tk.Button(frame_edicoes,
                  text="Adicionar",
                  bg="cyan",
                  width=10,
                  command=lambda: adicionar('dedução')).grid(row=1,
                                                             column=3,
                                                             padx=5,
                                                             pady=5,
                                                             sticky="eW"
                                                             )

def atualizar_comboboxes():
    '''
    Atualiza os widgets de combobox.
    '''
    tipos = ['material', 'espessura', 'canal']
    for tipo in tipos:
        atualizar_widgets(tipo)

def main(root):
    '''
    Inicializa e exibe o formulário de gerenciamento de deduções.
    '''
    configurar_janela(root)
    main_frame = configurar_main_frame(g.DEDUC_FORM)
    criar_frame_busca(main_frame)
    criar_lista_deducoes(main_frame)
    frame_edicoes = criar_frame_edicoes(main_frame)
    configurar_botoes(main_frame, frame_edicoes)
    atualizar_comboboxes()

if __name__ == "__main__":
    main(None)
