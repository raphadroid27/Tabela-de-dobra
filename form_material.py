import tkinter as tk
from tkinter import ttk
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from funcoes import *
import globals as g

# Configuração do banco de dados
engine = create_engine('sqlite:///tabela_de_dobra.db')
Session = sessionmaker(bind=engine)
session = Session()

def main(root):

    if g.MATER_FORM is not None:
        g.MATER_FORM.destroy()   
        pass

    g.MATER_FORM = tk.Toplevel()
    g.MATER_FORM.resizable(False, False)
    g.MATER_FORM.geometry("340x420")

    no_topo(g.MATER_FORM)
    posicionar_janela(g.MATER_FORM, None)

    main_frame = tk.Frame(g.MATER_FORM)
    main_frame.pack(pady=5, padx=5, fill='both', expand=True)

    main_frame.columnconfigure(0,weight=1)

    main_frame.rowconfigure(0,weight=0)
    main_frame.rowconfigure(1,weight=1)
    main_frame.rowconfigure(2,weight=0)
    main_frame.rowconfigure(3,weight=0)

    frame_busca = tk.LabelFrame(main_frame, text='Buscar Materiais', pady=5)
    frame_busca.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

    frame_busca.columnconfigure(0, weight=0)
    frame_busca.columnconfigure(1, weight=1)
    frame_busca.columnconfigure(2, weight=0)

    tk.Label(frame_busca, text="Nome:").grid(row=0,column=0)
    g.MAT_BUSCA_ENTRY=tk.Entry(frame_busca)
    g.MAT_BUSCA_ENTRY.grid(row=0, column=1, sticky="ew")
    g.MAT_BUSCA_ENTRY.bind("<KeyRelease>", lambda event: buscar('material'))

    tk.Button(frame_busca, text="Limpar", command = lambda: limpar_busca('material')).grid(row=0, column=2, padx=5, pady=5)

    columns = ("Id", "Nome", "Densidade", "Escoamento", "Elasticidade")
    g.LSIT_MAT = ttk.Treeview(main_frame, columns=columns, show="headings")
    for col in columns:
        g.LSIT_MAT["displaycolumns"] = ("Nome", "Densidade", "Escoamento", "Elasticidade")
        g.LSIT_MAT.heading(col, text=col)
        g.LSIT_MAT.column(col, anchor="center", width=20)    
    
    g.LSIT_MAT.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

    listar('material')

    frame_edicoes = tk.LabelFrame(main_frame, pady=5)
    frame_edicoes.grid(row=3, column=0, padx=5,pady=5, sticky="ew")

    frame_edicoes.columnconfigure(0, weight=1)
    frame_edicoes.columnconfigure(1, weight=1)
    frame_edicoes.columnconfigure(2, weight=0)

    frame_edicoes.rowconfigure(0, weight=1)
    frame_edicoes.rowconfigure(1, weight=1)
    frame_edicoes.rowconfigure(2, weight=1)
    frame_edicoes.rowconfigure(3, weight=1)

    tk.Label(frame_edicoes, text="Nome:", anchor="w").grid(row=0, column=0, padx=2, sticky='sw')
    g.MAT_NOME_ENTRY = tk.Entry(frame_edicoes)
    g.MAT_NOME_ENTRY.grid(row=1, column=0, padx=5, sticky="ew")

    tk.Label(frame_edicoes, text="Densidade:", anchor="w").grid(row=0, column=1, padx=2, sticky='sw')
    g.MAT_DENS_ENTRY = tk.Entry(frame_edicoes)
    g.MAT_DENS_ENTRY.grid(row=1, column=1, padx=5, sticky="ew")

    tk.Label(frame_edicoes, text="Escoamento:", anchor="w").grid(row=2, column=0, padx=2, sticky='sw')
    g.MAT_ESCO_ENTRY = tk.Entry(frame_edicoes)
    g.MAT_ESCO_ENTRY.grid(row=3, column=0, padx=5, sticky="ew")

    tk.Label(frame_edicoes, text="Elasticidade:", anchor="w").grid(row=2, column=1, padx=2, sticky='sw')
    g.MAT_ELAS_ENTRY = tk.Entry(frame_edicoes)
    g.MAT_ELAS_ENTRY.grid(row=3, column=1, padx=5, sticky="ew")

    if g.EDIT_MAT == True:
        g.MATER_FORM.title("Editar/Excluir Material")
        g.LSIT_MAT.bind("<ButtonRelease-1>", lambda event: preencher_campos('material'))
        frame_edicoes.config(text='Editar Material')
        
        tk.Button(main_frame, text="Excluir", command = lambda: excluir('material'), bg="red").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        tk.Button(frame_edicoes, text="Atualizar", command = lambda: editar('material'), bg="green").grid(row=1, column=2, padx=5, pady=5, sticky="ew", rowspan=3)
    else:
        g.MATER_FORM.title("Adicionar Material")
        frame_edicoes.config(text='Novo Material')
        tk.Button(frame_edicoes, text="Adicionar", command= lambda: adicionar('material'), bg="cyan").grid(row=1, column=2, padx=5, pady=5, sticky="ew", rowspan=3)

    g.MATER_FORM.mainloop()

if __name__ == "__main__":
    main(None)
