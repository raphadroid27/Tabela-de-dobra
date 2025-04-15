import tkinter as tk
from tkinter import ttk
from funcoes import (no_topo, posicionar_janela, buscar, limpar_busca,
                    listar, preencher_campos, excluir, editar, adicionar)
import globals as g
from styles import configurar_estilos

def main(root):
    """
    Inicializa e exibe o formulário de gerenciamento de canais.
    Configura a interface gráfica para adicionar, editar e excluir canais.
    """
    if g.CANAL_FORM:
        g.CANAL_FORM.destroy()

    g.CANAL_FORM = tk.Toplevel(root)
    g.CANAL_FORM.resizable(False, False)
    g.CANAL_FORM.geometry("340x420")
    no_topo(g.CANAL_FORM)
    posicionar_janela(g.CANAL_FORM, None)

    # Configurar estilos
    configurar_estilos()

    main_frame = ttk.Frame(g.CANAL_FORM)
    main_frame.pack(pady=5, padx=5, fill='both', expand=True)

    main_frame.columnconfigure(0, weight=1)
    for i in range(4):
        main_frame.rowconfigure(i, weight=1 if i == 1 else 0)

    # Criação do frame de busca
    frame_busca = ttk.Labelframe(main_frame, text='Buscar Canais')
    frame_busca.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

    for i in range(3):
        frame_busca.columnconfigure(i, weight=1 if i == 1 else 0)

    ttk.Label(frame_busca, text="Valor:", style="Titulo.TLabel").grid(row=0, column=0)
    g.CANAL_BUSCA_ENTRY = ttk.Entry(frame_busca, style="TEntry")
    g.CANAL_BUSCA_ENTRY.grid(row=0, column=1, sticky="ew")
    g.CANAL_BUSCA_ENTRY.bind("<Return>", lambda event: buscar('canal'))
    
    ttk.Button(frame_busca,
               text="Limpar",
               style="TButton",
               command=lambda: limpar_busca('canal')
               ).grid(row=0, column=2, padx=5, pady=5)

    # Treeview de canais
    columns = ("Id", "Canal", "Largura", "Altura", "Compr.", "Obs.")
    g.LIST_CANAL = ttk.Treeview(main_frame, columns=columns, show="headings", style="Treeview")
    g.LIST_CANAL["displaycolumns"] = ("Canal", "Largura", "Altura", "Compr.", "Obs.")
    for col in columns:
        g.LIST_CANAL.heading(col, text=col)
        g.LIST_CANAL.column(col, anchor="center", width=60)
    g.LIST_CANAL.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
    listar('canal')

    # Frame de edições
    frame_edicoes = ttk.LabelFrame(main_frame, padding=5)
    frame_edicoes.grid(row=3, column=0, padx=5, pady=5, sticky="ew")
    frame_edicoes.columnconfigure(0, weight=1)
    frame_edicoes.columnconfigure(1, weight=1)
    frame_edicoes.columnconfigure(2, weight=0)
    for i in range(4):
        frame_edicoes.rowconfigure(i, weight=1)

    ttk.Label(frame_edicoes, text="Valor:", anchor="w", style="TLabel").grid(row=0, column=0, padx=2, sticky='sw')
    g.CANAL_VALOR_ENTRY = ttk.Entry(frame_edicoes, style="TEntry")
    g.CANAL_VALOR_ENTRY.grid(row=1, column=0, padx=5, sticky="ew")

    ttk.Label(frame_edicoes, text="Largura:", anchor="w", style="TLabel").grid(row=0, column=1, padx=2, sticky='sw')
    g.CANAL_LARGU_ENTRY = ttk.Entry(frame_edicoes, style="TEntry")
    g.CANAL_LARGU_ENTRY.grid(row=1, column=1, padx=5, sticky="ew")

    ttk.Label(frame_edicoes, text="Altura:", anchor="w", style="TLabel").grid(row=2, column=0, padx=2, sticky='sw')
    g.CANAL_ALTUR_ENTRY = ttk.Entry(frame_edicoes, style="TEntry")
    g.CANAL_ALTUR_ENTRY.grid(row=3, column=0, padx=5, sticky="ew")

    ttk.Label(frame_edicoes, text="Comprimento total:", anchor="w", style="TLabel").grid(row=2, column=1, padx=2, sticky='sw')
    g.CANAL_COMPR_ENTRY = ttk.Entry(frame_edicoes, style="TEntry")
    g.CANAL_COMPR_ENTRY.grid(row=3, column=1, padx=5, sticky="ew")

    ttk.Label(frame_edicoes, text="Observação:", anchor="w", style="TLabel").grid(row=4, column=0, padx=2, sticky='sw')
    g.CANAL_OBSER_ENTRY = ttk.Entry(frame_edicoes, style="TEntry")
    g.CANAL_OBSER_ENTRY.grid(row=5, column=0, columnspan=2, padx=5, sticky="ew")

    # Botões de ação
    if g.EDIT_CANAL:
        g.CANAL_FORM.title("Editar/Excluir Canal")
        g.LIST_CANAL.bind("<<TreeviewSelect>>", lambda event: preencher_campos('canal'))
        frame_edicoes.config(text='Editar Canal')

        ttk.Button(main_frame, text="Excluir", style="Excluir.TButton", command=lambda: excluir('canal')).grid(row=2, column=0, padx=5, pady=5, sticky="e")
        ttk.Button(frame_edicoes, text="Atualizar", style="Atualizar.TButton", command=lambda: editar('canal')).grid(row=1, column=2, padx=5, pady=5, sticky="ew", rowspan=5)
    else:
        g.CANAL_FORM.title("Novo Canal")
        frame_edicoes.config(text='Novo Canal')

        ttk.Button(frame_edicoes, text="Adicionar", style="Adicionar.TButton", command=lambda: adicionar('canal')).grid(row=1, column=2, padx=5, pady=5, sticky="ew", rowspan=5)

    g.CANAL_FORM.mainloop()

if __name__ == "__main__":
    main(None)
