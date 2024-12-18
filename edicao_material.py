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

    root = tk.Tk()
    root.title("Editar/Excluir Material")
    root.resizable(False, False)

    main_frame = tk.Frame(root)
    main_frame.pack(pady=5, padx=5, fill='both', expand=True)

    columns = ("Nome", "Densidade", "Escoamento", "Elasticidade")
    g.lista_material = ttk.Treeview(main_frame, columns=columns, show="headings")
    for col in columns:
        g.lista_material.heading(col, text=col)
        g.lista_material.column(col, anchor="center", width=20)    
    
    g.lista_material.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

    carregar_lista_materiais()

    tk.Button(main_frame, text="Excluir", command=excluir_material, bg="red").grid(row=1, column=0, padx=5, pady=5, sticky="e")

    frame_edicoes = tk.LabelFrame(main_frame, text='Editar Material', pady=5)
    frame_edicoes.grid(row=2, column=0, padx=5, pady=5, sticky="ew")

    frame_edicoes.columnconfigure(0, weight=1)
    frame_edicoes.columnconfigure(1, weight=1)
    frame_edicoes.columnconfigure(2, weight=1)
    frame_edicoes.columnconfigure(3, weight=1)

    tk.Label(frame_edicoes, text="Nome:", anchor="w").grid(row=0, column=0, padx=2, sticky='sw')
    g.material_nome_entry = tk.Entry(frame_edicoes)
    g.material_nome_entry.grid(row=1, column=0, padx=5, sticky="ew")

    tk.Label(frame_edicoes, text="Densidade:", anchor="w").grid(row=0, column=1,padx=2, sticky='sw')
    g.material_densidade_entry = tk.Entry(frame_edicoes)
    g.material_densidade_entry.grid(row=1, column=1, padx=5, sticky="ew")

    tk.Label(frame_edicoes, text="Escoamento:", anchor="w").grid(row=2, padx=2, column=0, sticky='sw')
    g.material_escoamento_entry = tk.Entry(frame_edicoes)
    g.material_escoamento_entry.grid(row=3, column=0, padx=5, sticky="ew")

    tk.Label(frame_edicoes, text="Elasticidade:", anchor="w").grid(row=2, column=1, padx=2, sticky='sw')
    g.material_elasticidade_entry = tk.Entry(frame_edicoes)
    g.material_elasticidade_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

    tk.Button(frame_edicoes, text="Atualizar", command=editar_material, bg="green").grid(row=1, column=4, padx=5, pady=5, sticky="ew", rowspan=3)

    root.mainloop()

if __name__ == "__main__":
    main(None)
