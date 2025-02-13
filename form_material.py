import tkinter as tk
from tkinter import ttk, messagebox
from models import material
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from funcoes import *
import globals as g

# Configuração do banco de dados
engine = create_engine('sqlite:///tabela_de_dobra.db')
Session = sessionmaker(bind=engine)
session = Session()

def main(root_app):

    if g.material_form is not None:
        g.material_form.destroy()   
        pass

    g.material_form = tk.Toplevel()
    g.material_form.resizable(False, False)
    g.material_form.geometry("340x420")

    def on_top_material():
        if g.on_top_var.get() == 1:
            g.material_form.attributes("-topmost", True)
        else:
            g.material_form.attributes("-topmost", False)
    
    on_top_material()

    # Posicionar a janela nova_deducao em relação à janela principal
    g.material_form.update_idletasks() 
    x = root_app.winfo_x() + root_app.winfo_width() + 10
    y = root_app.winfo_y()
    g.material_form.geometry(f"+{x}+{y}")

    main_frame = tk.Frame(g.material_form)
    main_frame.pack(pady=5, padx=5, fill='both', expand=True)

    main_frame.columnconfigure(0,weight=1)

    main_frame.rowconfigure(0,weight=0)
    main_frame.rowconfigure(1,weight=1)
    main_frame.rowconfigure(2,weight=0)
    main_frame.rowconfigure(3,weight=0)

    frame_busca = tk.LabelFrame(main_frame, text='Filtrar Materiais', pady=5)
    frame_busca.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

    frame_busca.columnconfigure(0, weight=0)
    frame_busca.columnconfigure(1, weight=1)
    frame_busca.columnconfigure(2, weight=0)

    tk.Label(frame_busca, text="Material:").grid(row=0,column=0)
    g.material_nome_entry=tk.Entry(frame_busca)
    g.material_nome_entry.grid(row=0, column=1, sticky="ew")

    tk.Button(frame_busca, text="Buscar", command=buscar_material).grid(row=0, column=3, padx=5, pady=5)
    tk.Button(frame_busca, text="Limpar", command=limpar_busca_material).grid(row=0, column=4, padx=5, pady=5)

    columns = ("Nome", "Densidade", "Escoamento", "Elasticidade")
    g.lista_material = ttk.Treeview(main_frame, columns=columns, show="headings")
    for col in columns:
        g.lista_material.heading(col, text=col)
        g.lista_material.column(col, anchor="center", width=20)    
    
    g.lista_material.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

    carregar_lista_material()

    frame_edicoes = tk.LabelFrame(main_frame, text='Editar Material', pady=5)
    frame_edicoes.grid(row=3, column=0, padx=5, pady=5, sticky="ew")

    frame_edicoes.columnconfigure(0, weight=1)
    frame_edicoes.columnconfigure(1, weight=1)

    tk.Label(frame_edicoes, text="Densidade:", anchor="w").grid(row=0, column=0,padx=2, sticky='sw')
    g.material_densidade_entry = tk.Entry(frame_edicoes)
    g.material_densidade_entry.grid(row=1, column=0, padx=5, sticky="ew")

    tk.Label(frame_edicoes, text="Escoamento:", anchor="w").grid(row=0, padx=2, column=1, sticky='sw')
    g.material_escoamento_entry = tk.Entry(frame_edicoes)
    g.material_escoamento_entry.grid(row=1, column=1, padx=5, sticky="ew")

    tk.Label(frame_edicoes, text="Elasticidade:", anchor="w").grid(row=2, column=0, padx=2, sticky='sw')
    g.material_elasticidade_entry = tk.Entry(frame_edicoes)
    g.material_elasticidade_entry.grid(row=3, column=0, padx=5, pady=5, sticky="ew")

    if g.editar_material == True:
        g.material_form.title("Editar/Excluir Material")
        tk.Button(main_frame, text="Excluir", command=excluir_material, bg="red").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        tk.Button(frame_edicoes, text="Atualizar", command=editar_material, bg="green").grid(row=1, column=2, padx=5, pady=5, sticky="ew", rowspan=3)
    else:
        g.material_form.title("Adicionar Material")
        tk.Button(frame_edicoes, text="Adicionar", command=novo_material, bg="cyan").grid(row=1, column=2, padx=5, pady=5, sticky="ew", rowspan=3)


    g.material_form.mainloop()

if __name__ == "__main__":
    main(None)
