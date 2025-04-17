'''
# Formulário de Espessura
# Este módulo implementa a interface gráfica para gerenciar espessuras de materiais.
# Ele permite adicionar, editar e excluir registros de espessuras, utilizando a
# biblioteca tkinter para a construção da interface. As variáveis globais são
# gerenciadas pelo módulo `globals`, enquanto as operações de banco de dados
# são realizadas pelo módulo `funcoes`.
'''
import os
import tkinter as tk
from tkinter import ttk
from src.config import globals as g
from src.utils.funcoes import (no_topo, posicionar_janela, buscar,
                     limpar_busca, listar, adicionar, excluir)


def main(root):
    """
    Inicializa a janela de gerenciamento de espessuras.
    Configura a interface gráfica para adicionar, editar e excluir espessuras.
    """
    if g.ESPES_FORM:
        g.ESPES_FORM.destroy()

    g.ESPES_FORM = tk.Toplevel(root)
    g.ESPES_FORM.geometry("240x280")
    g.ESPES_FORM.resizable(False, False)

    # Define o ícone
    icon_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'icone.ico')
    )
    g.ESPES_FORM.iconbitmap(icon_path)

    no_topo(g.ESPES_FORM)
    posicionar_janela(g.ESPES_FORM,None)

    main_frame = tk.Frame(g.ESPES_FORM)
    main_frame.pack(pady=5, padx=5, fill='both', expand=True)

    main_frame.columnconfigure(0,weight=1)

    main_frame.rowconfigure(0,weight=0)
    main_frame.rowconfigure(1,weight=1)
    main_frame.rowconfigure(2,weight=0)
    main_frame.rowconfigure(3,weight=0)

    frame_busca = tk.LabelFrame(main_frame, text='Buscar Espessuras', pady=5)
    frame_busca.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

    frame_busca.columnconfigure(0, weight=0)
    frame_busca.columnconfigure(1, weight=1)
    frame_busca.columnconfigure(2, weight=0)

    tk.Label(frame_busca, text="Valor:").grid(row=0,column=0)
    g.ESP_BUSCA_ENTRY=tk.Entry(frame_busca)
    g.ESP_BUSCA_ENTRY.grid(row=0, column=1, sticky="ew")
    g.ESP_BUSCA_ENTRY.bind("<KeyRelease>", lambda event: buscar('espessura'))

    tk.Button(frame_busca,
              text="Limpar",
              command = lambda: limpar_busca('espessura')).grid(row=0, column=2, padx=5, pady=5)

    columns = ("Id","Valor")
    g.LIST_ESP = ttk.Treeview(main_frame, columns=columns, show="headings")
    for col in columns:
        g.LIST_ESP["displaycolumns"] = "Valor"
        g.LIST_ESP.heading(col, text=col)
        g.LIST_ESP.column(col, anchor="center")

    g.LIST_ESP.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

    listar('espessura')

    if g.EDIT_ESP:
        g.ESPES_FORM.title("Editar/Excluir Espessura")
        tk.Button(main_frame,
                  text="Excluir",
                  command=lambda:excluir('espessura'),
                  bg="red").grid(row=2, column=0, padx=5, pady=5, sticky="e")
    else:
        g.ESPES_FORM.title("Adicionar Espessura")

        frame_edicoes = tk.LabelFrame(main_frame, text='Nova Espessura', pady=5)
        frame_edicoes.grid(row=3, column=0, padx=5,pady=5, sticky="ew")

        frame_edicoes.columnconfigure(0, weight=1)
        frame_edicoes.columnconfigure(1, weight=2)
        frame_edicoes.columnconfigure(2, weight=0)

        tk.Label(frame_edicoes, text="Valor:").grid(row=0, column=0, sticky="w", padx=5)
        g.ESP_VALOR_ENTRY = tk.Entry(frame_edicoes)
        g.ESP_VALOR_ENTRY.grid(row=0, column=1, sticky="ew")
        tk.Button(frame_edicoes,
                  text="Adicionar",
                  command = lambda: adicionar('espessura'),
                  bg="cyan").grid(row=0, column=2, padx=5, pady=5, sticky="e")

    g.ESPES_FORM.mainloop()

if __name__ == "__main__":
    main(None)
