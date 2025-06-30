"""
# Formulário de Espessura
# Este módulo implementa a interface gráfica para gerenciar espessuras de materiais.
# Ele permite adicionar, editar e excluir registros de espessuras, utilizando a
# biblioteca tkinter para a construção da interface. As variáveis globais são
# gerenciadas pelo módulo `globals`, enquanto as operações de banco de dados
# são realizadas pelo módulo `funcoes`.
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
                                      excluir,
                                      adicionar
                                      )
from src.config import globals as g

def configurar_janela(root):
    """
    Configura a janela principal do formulário de espessuras.
    """
    if g.ESPES_FORM:
        g.ESPES_FORM.destroy()

    g.ESPES_FORM = tk.Toplevel(root)
    g.ESPES_FORM.geometry("240x280")
    g.ESPES_FORM.resizable(False, False)

    icone_path = obter_caminho_icone()
    g.ESPES_FORM.iconbitmap(icone_path)

    no_topo(g.ESPES_FORM)
    posicionar_janela(g.ESPES_FORM, None)

def criar_frame_busca(main_frame):
    """
    Cria o frame de busca.
    """
    frame_busca = tk.LabelFrame(main_frame, text='Buscar Espessuras', pady=5)
    frame_busca.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

    for i in range(3):
        frame_busca.columnconfigure(i, weight=1 if i == 1 else 0)

    tk.Label(frame_busca, text="Valor:").grid(row=0, column=0)
    g.ESP_BUSCA_ENTRY = tk.Entry(frame_busca)
    g.ESP_BUSCA_ENTRY.grid(row=0, column=1, sticky="ew")
    g.ESP_BUSCA_ENTRY.bind("<KeyRelease>", lambda event: buscar('espessura'))

    tk.Button(frame_busca,
              text="Limpar",
              bg='lightyellow',
              command=lambda: limpar_busca('espessura')).grid(row=0, column=2, padx=5, pady=5)

def criar_lista_espessuras(main_frame):
    """
    Cria a lista de espessuras.
    """
    columns = ("Id", "Valor")
    g.LIST_ESP = ttk.Treeview(main_frame, columns=columns, show="headings")
    g.LIST_ESP["displaycolumns"] = "Valor"
    for col in columns:
        g.LIST_ESP.heading(col, text=col)
        g.LIST_ESP.column(col, anchor="center")

    g.LIST_ESP.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
    listar('espessura')

def criar_frame_edicoes(main_frame):
    """
    Cria o frame de edições.
    """
    frame_edicoes = configurar_frame_edicoes(main_frame,
                                             text='Adicionar Espessura'
                                             if not g.EDIT_ESP
                                             else 'Editar Espessura'
                                             )

    tk.Label(frame_edicoes, text="Valor:").grid(row=0, column=0, sticky="w", padx=5)
    g.ESP_VALOR_ENTRY = tk.Entry(frame_edicoes)
    g.ESP_VALOR_ENTRY.grid(row=0, column=1, sticky="ew")
    tk.Button(frame_edicoes,
              text="Adicionar",
              command=lambda: adicionar('espessura'),
              bg="lightblue").grid(row=0, column=2, padx=5, pady=5, sticky="e")

def configurar_botoes(main_frame):
    """
    Configura os botões de ação (Excluir).
    """
    if g.ESPES_FORM is not None:
        if g.EDIT_ESP:
            g.ESPES_FORM.title("Editar/Excluir Espessura")
            tk.Button(main_frame,
                      text="Excluir",
                      command=lambda: excluir('espessura'),
                      bg="lightcoral").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        else:
            g.ESPES_FORM.title("Adicionar Espessura")
    else:
        print("Erro: g.ESPES_FORM não foi inicializado.")

def main(root):
    """
    Inicializa e exibe o formulário de gerenciamento de espessuras.
    """
    configurar_janela(root)
    main_frame = configurar_main_frame(g.ESPES_FORM)
    criar_frame_busca(main_frame)
    criar_lista_espessuras(main_frame)
    if not g.EDIT_ESP:
        criar_frame_edicoes(main_frame)
    configurar_botoes(main_frame)

if __name__ == "__main__":
    main(None)
