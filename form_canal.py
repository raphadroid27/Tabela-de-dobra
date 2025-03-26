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

def main(root_app):

    if g.canal_form is not None:
        g.canal_form.destroy()
        pass

    g.canal_form = tk.Toplevel()
    g.canal_form.resizable(False, False)
    g.canal_form.geometry("340x420")

    no_topo(g.canal_form)
    posicionar_janela(g.canal_form,None)

    main_frame = tk.Frame(g.canal_form)
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
    g.canal_busca_entry=tk.Entry(frame_busca)
    g.canal_busca_entry.grid(row=0, column=1, sticky="ew")
    g.canal_busca_entry.bind("<KeyRelease>", lambda event: buscar('canal'))

    tk.Button(frame_busca, text="Limpar", command =lambda:limpar_busca('canal')).grid(row=0, column=2, padx=5, pady=5)

    columns = ("Id","Canal", "Largura", "Altura", "Compr.", "Obs.")
    g.lista_canal = ttk.Treeview(main_frame, columns=columns, show="headings")
    for col in columns:
        g.lista_canal["displaycolumns"] = ("Canal", "Largura", "Altura", "Compr.", "Obs.")
        g.lista_canal.heading(col, text=col)
        g.lista_canal.column(col, anchor="center", width=20)    
    
    g.lista_canal.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

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
    g.canal_valor_entry = tk.Entry(frame_edicoes)
    g.canal_valor_entry.grid(row=1, column=0, padx=5, sticky="ew")

    tk.Label(frame_edicoes, text="Largura:", anchor="w").grid(row=0, padx=2, column=1, sticky='sw')
    g.canal_largura_entry = tk.Entry(frame_edicoes)
    g.canal_largura_entry.grid(row=1, column=1, padx=5, sticky="ew")

    tk.Label(frame_edicoes, text="Altura:", anchor="w").grid(row=2, column=0, padx=2, sticky='sw')
    g.canal_altura_entry = tk.Entry(frame_edicoes)
    g.canal_altura_entry.grid(row=3, column=0, padx=5, sticky="ew")

    tk.Label(frame_edicoes, text="Comprimento total:", anchor="w").grid(row=2, column=1, padx=2, sticky='sw')
    g.canal_comprimento_entry = tk.Entry(frame_edicoes)
    g.canal_comprimento_entry.grid(row=3, column=1, padx=5, sticky="ew")

    tk.Label(frame_edicoes, text="Observação:", anchor="w").grid(row=4, column=0, padx=2, sticky='sw')
    g.canal_observacao_entry = tk.Entry(frame_edicoes)
    g.canal_observacao_entry.grid(row=5, column=0, columnspan=2, padx=5, sticky="ew")


    if g.editar_canal == True:     
        g.canal_form.title("Editar/Excluir Canal")
        g.lista_canal.bind("<ButtonRelease-1>", lambda event: preencher_campos('canal'))
        frame_edicoes.config(text='Editar Canal')

        tk.Button(main_frame, text="Excluir", command=lambda:excluir('canal'), bg="red").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        tk.Button(frame_edicoes, text="Atualizar", command=lambda:editar('canal'), bg="green").grid(row=1, column=2, padx=5, pady=5, sticky="ew",rowspan=5)
    else:  
        g.canal_form.title("Novo Canal")
        frame_edicoes.config(text='Novo Canal')
        tk.Button(frame_edicoes, text="Adicionar", command=lambda:adicionar('canal'), bg="cyan").grid(row=1, column=2, padx=5, pady=5, sticky="ew",rowspan=5)

    g.canal_form.mainloop()

if __name__ == "__main__":
    main(None)
