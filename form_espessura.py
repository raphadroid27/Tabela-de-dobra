import tkinter as tk
from tkinter import ttk
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from funcoes import *

# Configuração do banco de dados
engine = create_engine('sqlite:///tabela_de_dobra.db')
Session = sessionmaker(bind=engine)
session = Session()

def main(root_app):

    if g.espessura_form is not None:
        g.espessura_form.destroy()   
        pass

    g.espessura_form = tk.Toplevel()
    g.espessura_form.geometry("240x280")
    g.espessura_form.resizable(False, False)

    no_topo(g.espessura_form)
    posicionar_janela(g.espessura_form, 'esquerda')

    main_frame = tk.Frame(g.espessura_form)
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
    g.espessura_busca_entry=tk.Entry(frame_busca)
    g.espessura_busca_entry.grid(row=0, column=1, sticky="ew")
    g.espessura_busca_entry.bind("<KeyRelease>", lambda event: buscar('espessura'))

    tk.Button(frame_busca, text="Limpar", command = lambda: limpar_busca('espessura')).grid(row=0, column=2, padx=5, pady=5)

    columns = ("Id","Valor")
    g.lista_espessura = ttk.Treeview(main_frame, columns=columns, show="headings")
    for col in columns:
        g.lista_espessura["displaycolumns"] = ("Valor")
        g.lista_espessura.heading(col, text=col)
        g.lista_espessura.column(col, anchor="center")    
    
    g.lista_espessura.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

    listar('espessura')

    if g.editar_espessura == True:
        g.espessura_form.title("Editar/Excluir Espessura")
        tk.Button(main_frame, text="Excluir", command=lambda:excluir('espessura'), bg="red").grid(row=2, column=0, padx=5, pady=5, sticky="e")
    else:
        g.espessura_form.title("Adicionar Espessura")
        
        frame_edicoes = tk.LabelFrame(main_frame, text='Nova Espessura', pady=5)
        frame_edicoes.grid(row=3, column=0, padx=5,pady=5, sticky="ew")

        frame_edicoes.columnconfigure(0, weight=1)
        frame_edicoes.columnconfigure(1, weight=2)
        frame_edicoes.columnconfigure(2, weight=0)

        tk.Label(frame_edicoes, text="Valor:").grid(row=0, column=0, sticky="w", padx=5)
        g.espessura_valor_entry = tk.Entry(frame_edicoes)
        g.espessura_valor_entry.grid(row=0, column=1, sticky="ew")
        tk.Button(frame_edicoes, text="Adicionar", command = lambda: adicionar('espessura'), bg="cyan").grid(row=0, column=2, padx=5, pady=5, sticky="e")

    g.espessura_form.mainloop()

if __name__ == "__main__":
    main(None)
