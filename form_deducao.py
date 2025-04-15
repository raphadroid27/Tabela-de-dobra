"""
# Formulário de Dedução
# Este módulo implementa o formulário de dedução, permitindo a adição, edição
# e exclusão de deduções. Ele utiliza a biblioteca tkinter para a interface
# gráfica, o módulo globals para variáveis globais e o módulo funcoes para
# operações relacionadas ao banco de dados.
"""
import tkinter as tk
from tkinter import ttk
import globals as g
from funcoes import (no_topo, posicionar_janela, buscar, limpar_busca, preencher_campos,
                     listar, adicionar, editar, excluir, atualizar_combobox)
from styles import configurar_estilos


def main(root):
    """
    Função principal que inicializa e configura o formulário de deduções.
    """
    # Verificar se a janela já está aberta
    if g.DEDUC_FORM:
        g.DEDUC_FORM.destroy()

    g.DEDUC_FORM = tk.Toplevel(root)
    g.DEDUC_FORM.geometry("500x420")
    g.DEDUC_FORM.resizable(False, False)

    no_topo(g.DEDUC_FORM)
    posicionar_janela(g.DEDUC_FORM, None)

    # Configurar estilos
    configurar_estilos()

    main_frame = ttk.Frame(g.DEDUC_FORM)
    main_frame.pack(pady=5, padx=5, fill='both', expand=True)

    main_frame.columnconfigure(0, weight=1)

    for i in [0, 2, 3]:
        main_frame.rowconfigure(i, weight=0)
    main_frame.rowconfigure(1, weight=1)

    frame_busca = ttk.LabelFrame(main_frame, text='Buscar Deduções')
    frame_busca.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

    for i in range(4):
        frame_busca.columnconfigure(i, weight=1)

    campos = [("Material", 0, "MATER"), ("Espessura", 1, "ESPES"), ("Canal", 2, "CANAL")]
    for texto, coluna, var in campos:
        ttk.Label(frame_busca, text=f"{texto}:", style="Titulo.TLabel").grid(row=0, column=coluna, padx=2, sticky='sw')
        combobox = ttk.Combobox(frame_busca)
        combobox.grid(row=1, column=coluna, padx=5, sticky="ew")
        combobox.bind("<<ComboboxSelected>>", lambda event, t='dedução': buscar(t))
        setattr(g, f"DED_{var.upper()}_COMB", combobox)

    ttk.Button(frame_busca,
              text="Limpar",
              width=10,
              style="TButton",
              command = lambda: limpar_busca('dedução')
              ).grid(row=1, column=3, padx=5, pady=5, sticky="e")

    columns = ("Id","Material", "Espessura","Canal", "Dedução", "Observação", "Força")
    g.LIST_DED = ttk.Treeview(main_frame, columns=columns, show="headings")
    for col in columns:
        g.LIST_DED["displaycolumns"] = ("Material",
                                        "Espessura",
                                        "Canal", "Dedução",
                                        "Observação",
                                        "Força")
        g.LIST_DED.heading(col, text=col)
        g.LIST_DED.column(col, anchor="center", width=60)
        g.LIST_DED.column("Material", width=80)
        g.LIST_DED.column("Observação", width=120, anchor="w")

    g.LIST_DED.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

    listar('dedução')

    frame_edicoes = ttk.LabelFrame(main_frame)
    frame_edicoes.grid(row=3, column=0, padx=5, pady=5, sticky="ew")

    for i in range(4):
        frame_edicoes.columnconfigure(i, weight=1)

    ttk.Label(frame_edicoes, text="Valor:").grid(row=0, column=0, padx=2, sticky='sw')
    g.DED_VALOR_ENTRY = ttk.Entry(frame_edicoes)
    g.DED_VALOR_ENTRY.grid(row=1, column=0, padx=5, sticky="ew")

    ttk.Label(frame_edicoes, text="Observação:").grid(row=0, column=1,padx=2, sticky='sw')
    g.DED_OBSER_ENTRY = ttk.Entry(frame_edicoes)
    g.DED_OBSER_ENTRY.grid(row=1, column=1, padx=5, sticky="ew")

    ttk.Label(frame_edicoes, text="Força:").grid(row=0, padx=2, column=2, sticky='sw')
    g.DED_FORCA_ENTRY = ttk.Entry(frame_edicoes)
    g.DED_FORCA_ENTRY.grid(row=1, column=2, padx=5, sticky="ew")

    if g.EDIT_DED is True:
        g.DEDUC_FORM.title("Editar/Excluir Dedução")
        g.LIST_DED.bind("<ButtonRelease-1>", lambda event: preencher_campos('dedução'))
        frame_edicoes.config(text='Editar Dedução')

        ttk.Button(frame_edicoes,
                  text="Atualizar",
                  width=10,
                  style="Atualizar.TButton",
                  command = lambda: editar('dedução')).grid(row=1,
                                                            column=3,
                                                            padx=5,
                                                            pady=5,
                                                            sticky="eW")
        ttk.Button(main_frame,
                  text="Excluir",
                  width=10,
                  style="Excluir.TButton",
                  command = lambda: excluir('dedução')).grid(row=2,
                                                             column=0,
                                                             padx=5,
                                                             pady=5,
                                                             sticky="e")
    else:
        g.DEDUC_FORM.title("Adicionar Dedução")
        frame_edicoes.config(text='Nova Dedução')
        ttk.Button(frame_edicoes,
                  text="Adicionar",
                  width=10,
                  command = lambda: adicionar('dedução')).grid(row=1,
                                                               column=3,
                                                               padx=5,
                                                               pady=5,
                                                               sticky="eW")

    tipos = ['material', 'espessura', 'canal']
    for tipo in tipos:
        atualizar_combobox(tipo)

    g.DEDUC_FORM.mainloop()

if __name__ == "__main__":
    main(None)
