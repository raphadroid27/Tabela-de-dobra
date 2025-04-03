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

    if g.CANAL_FORM is not None:
        g.CANAL_FORM.destroy()
        pass

    g.CANAL_FORM = tk.Toplevel()
    g.CANAL_FORM.resizable(False, False)
    g.CANAL_FORM.geometry("340x420")

    no_topo(g.CANAL_FORM)
    posicionar_janela(g.CANAL_FORM,None)

    main_frame = tk.Frame(g.CANAL_FORM)
    main_frame.pack(pady=5, padx=5, fill='both', expand=True)

    main_frame.columnconfigure(0,weight=1)

    main_frame.rowconfigure(0,weight=0)
    main_frame.rowconfigure(1,weight=1)
    main_frame.rowconfigure(2,weight=0)
    main_frame.rowconfigure(3,weight=0)

    frame_busca = tk.LabelFrame(main_frame, text='Buscar Canais', pady=5)
    frame_busca.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

    frame_busca.columnconfigure(0, weight=0)
    frame_busca.columnconfigure(1, weight=1)
    frame_busca.columnconfigure(2, weight=0)
    
    tk.Label(frame_busca, text="Valor:").grid(row=0,column=0)
    g.CANAL_BUSCA_ENTRY=tk.Entry(frame_busca)
    g.CANAL_BUSCA_ENTRY.grid(row=0, column=1, sticky="ew")
    g.CANAL_BUSCA_ENTRY.bind("<KeyRelease>", lambda event: buscar('canal'))

    tk.Button(frame_busca, text="Limpar", command =lambda:limpar_busca('canal')).grid(row=0, column=2, padx=5, pady=5)

    columns = ("Id","Canal", "Largura", "Altura", "Compr.", "Obs.")
    g.LIST_CANAL = ttk.Treeview(main_frame, columns=columns, show="headings")
    for col in columns:
        g.LIST_CANAL["displaycolumns"] = ("Canal", "Largura", "Altura", "Compr.", "Obs.")
        g.LIST_CANAL.heading(col, text=col)
        g.LIST_CANAL.column(col, anchor="center", width=20)    
    
    g.LIST_CANAL.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

    listar('canal')

    frame_edicoes = tk.LabelFrame(main_frame, pady=5)
    frame_edicoes.grid(row=3, column=0, padx=5, pady=5, sticky="ew")

    frame_edicoes.columnconfigure(0, weight=1)
    frame_edicoes.columnconfigure(1, weight=1)
    frame_edicoes.columnconfigure(2, weight=0)

    frame_edicoes.rowconfigure(0, weight=1)
    frame_edicoes.rowconfigure(1, weight=1)
    frame_edicoes.rowconfigure(2, weight=1)
    frame_edicoes.rowconfigure(3, weight=1)

    tk.Label(frame_edicoes, text="Valor:", anchor="w").grid(row=0, column=0,padx=2, sticky='sw')
    g.CANAL_VALOR_ENTRY = tk.Entry(frame_edicoes)
    g.CANAL_VALOR_ENTRY.grid(row=1, column=0, padx=5, sticky="ew")

    tk.Label(frame_edicoes, text="Largura:", anchor="w").grid(row=0, padx=2, column=1, sticky='sw')
    g.CANAL_LARGU_ENTRY = tk.Entry(frame_edicoes)
    g.CANAL_LARGU_ENTRY.grid(row=1, column=1, padx=5, sticky="ew")

    tk.Label(frame_edicoes, text="Altura:", anchor="w").grid(row=2, column=0, padx=2, sticky='sw')
    g.CANAL_ALTUR_ENTRY = tk.Entry(frame_edicoes)
    g.CANAL_ALTUR_ENTRY.grid(row=3, column=0, padx=5, sticky="ew")

    tk.Label(frame_edicoes, text="Comprimento total:", anchor="w").grid(row=2, column=1, padx=2, sticky='sw')
    g.CANAL_COMPR_ENTRY = tk.Entry(frame_edicoes)
    g.CANAL_COMPR_ENTRY.grid(row=3, column=1, padx=5, sticky="ew")

    tk.Label(frame_edicoes, text="Observação:", anchor="w").grid(row=4, column=0, padx=2, sticky='sw')
    g.CANAL_OBSER_ENTRY = tk.Entry(frame_edicoes)
    g.CANAL_OBSER_ENTRY.grid(row=5, column=0, columnspan=2, padx=5, sticky="ew")


    if g.EDIT_CANAL == True:     
        g.CANAL_FORM.title("Editar/Excluir Canal")
        g.LIST_CANAL.bind("<ButtonRelease-1>", lambda event: preencher_campos('canal'))
        frame_edicoes.config(text='Editar Canal')

        tk.Button(main_frame, text="Excluir", command=lambda:excluir('canal'), bg="red").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        tk.Button(frame_edicoes, text="Atualizar", command=lambda:editar('canal'), bg="green").grid(row=1, column=2, padx=5, pady=5, sticky="ew",rowspan=5)
    else:  
        g.CANAL_FORM.title("Novo Canal")
        frame_edicoes.config(text='Novo Canal')
        tk.Button(frame_edicoes, text="Adicionar", command=lambda:adicionar('canal'), bg="cyan").grid(row=1, column=2, padx=5, pady=5, sticky="ew",rowspan=5)

    g.CANAL_FORM.mainloop()

if __name__ == "__main__":
    main(None)
