import tkinter as tk
from tkinter import ttk
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import globals as g
from funcoes import *

# Configuração do banco de dados
engine = create_engine('sqlite:///tabela_de_dobra.db')
Session = sessionmaker(bind=engine)
session = Session()

def main(root):
    # Verificar se a janela já está aberta
    if g.DEDUC_FORM is not None:
        g.DEDUC_FORM.destroy()   
        pass
    
    g.DEDUC_FORM = tk.Toplevel()
    g.DEDUC_FORM.geometry("500x420")
    g.DEDUC_FORM.resizable(False, False)

    no_topo(g.DEDUC_FORM)
    posicionar_janela(g.DEDUC_FORM, None)
    
    main_frame = tk.Frame(g.DEDUC_FORM)
    main_frame.pack(pady=5, padx=5, fill='both', expand=True)

    main_frame.columnconfigure(0, weight=1)

    main_frame.rowconfigure(0, weight=0)
    main_frame.rowconfigure(1, weight=1)
    main_frame.rowconfigure(2, weight=0)
    main_frame.rowconfigure(3, weight=0)

    frame_busca = tk.LabelFrame(main_frame, text='Buscar Deduções', pady=5)
    frame_busca.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

    frame_busca.columnconfigure(0, weight=1)
    frame_busca.columnconfigure(1, weight=1)
    frame_busca.columnconfigure(2, weight=1)
    frame_busca.columnconfigure(3, weight=0)

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

    tk.Button(frame_busca, text="Limpar", command = lambda: limpar_busca('dedução')).grid(row=1, column=3, padx=5, pady=5)

    columns = ("Id","Material", "Espessura","Canal", "Dedução", "Observação", "Força")
    g.LIST_DED = ttk.Treeview(main_frame, columns=columns, show="headings")
    for col in columns:
        g.LIST_DED["displaycolumns"] = ("Material", "Espessura", "Canal", "Dedução", "Observação", "Força")
        g.LIST_DED.heading(col, text=col)
        g.LIST_DED.column(col, anchor="center", width=60)
        g.LIST_DED.column("Material", width=80)
        g.LIST_DED.column("Observação", width=120, anchor="w")

    g.LIST_DED.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
    
    listar('dedução')

    frame_edicoes = tk.LabelFrame(main_frame, pady=5)
    frame_edicoes.grid(row=3, column=0, padx=5, pady=5, sticky="ew")

    frame_edicoes.columnconfigure(0, weight=2)
    frame_edicoes.columnconfigure(1, weight=2)
    frame_edicoes.columnconfigure(2, weight=2)
    frame_edicoes.columnconfigure(3, weight=1)

    tk.Label(frame_edicoes, text="Valor:").grid(row=0, column=0, padx=2, sticky='sw')
    g.DED_VALOR_ENTRY = tk.Entry(frame_edicoes)
    g.DED_VALOR_ENTRY.grid(row=1, column=0, padx=5, sticky="ew")

    tk.Label(frame_edicoes, text="Observação:").grid(row=0, column=1,padx=2, sticky='sw')
    g.DED_OBSER_ENTRY = tk.Entry(frame_edicoes)
    g.DED_OBSER_ENTRY.grid(row=1, column=1, padx=5, sticky="ew")

    tk.Label(frame_edicoes, text="Força:").grid(row=0, padx=2, column=2, sticky='sw')
    g.DED_FORCA_ENTRY = tk.Entry(frame_edicoes)
    g.DED_FORCA_ENTRY.grid(row=1, column=2, padx=5, sticky="ew")


    if g.EDIT_DED == True:
        g.DEDUC_FORM.title("Editar/Excluir Dedução")
        g.LIST_DED.bind("<ButtonRelease-1>", lambda event: preencher_campos('dedução'))
        frame_edicoes.config(text='Editar Dedução')
        
        tk.Button(frame_edicoes, text="Atualizar", command = lambda: editar('dedução'), bg="green").grid(row=1, column=3, padx=5, pady=5, sticky="eW")       
        tk.Button(main_frame, text="Excluir", command = lambda: excluir('dedução'), bg="red").grid(row=2, column=0, padx=5, pady=5,sticky="e")
    else:
        g.DEDUC_FORM.title("Adicionar Dedução")
        frame_edicoes.config(text='Nova Dedução')
        tk.Button(frame_edicoes, text="Adicionar", command = lambda: adicionar('dedução'), bg="cyan").grid(row=1, column=3, padx=5, pady=5, sticky="eW")

    atualizar_combobox_deducao()
          
    g.DEDUC_FORM.mainloop()

if __name__ == "__main__":
    main(None)