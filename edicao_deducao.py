import tkinter as tk
from tkinter import ttk, messagebox
from models import deducao, espessura, material, canal
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import globals as g
from funcoes import *

# Configuração do banco de dados
engine = create_engine('sqlite:///tabela_de_dobra.db')
Session = sessionmaker(bind=engine)
session = Session()

def main(root_app):

    root = tk.Tk()
    root.title("Editar/Excluir Dedução")
    root.resizable(False, False)

    main_frame = tk.Frame(root)
    main_frame.pack(pady=5, padx=5)

    columns = ("Material", "Espessura","Canal", "Dedução", "Observação", "Força")
    g.tree = ttk.Treeview(main_frame, columns=columns, show="headings")
    for col in columns:
        g.tree.heading(col, text=col)
        g.tree.column(col, anchor="center", width=60)
        g.tree.column("Material", width=80)
        g.tree.column("Observação", width=120, anchor="w")

    g.tree.pack()

    carregar_deducoes()

    frame_edicoes = tk.Frame(root)
    frame_edicoes.pack(pady=5, padx=5)

    frame_edicoes.columnconfigure(0, weight=1)
    frame_edicoes.columnconfigure(1, weight=1)
    frame_edicoes.columnconfigure(2, weight=1)
    frame_edicoes.columnconfigure(3, weight=1)
    frame_edicoes.columnconfigure(4, weight=1)

    tk.Label(frame_edicoes, text="Novo Valor:", anchor="w").grid(row=0, column=0, sticky="w")
    g.deducao_valor_entry = tk.Entry(frame_edicoes)
    g.deducao_valor_entry.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

    tk.Label(frame_edicoes, text="Nova Observação:", anchor="w").grid(row=0, column=1, sticky="w")
    g.deducao_obs_entry = tk.Entry(frame_edicoes)
    g.deducao_obs_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

    tk.Label(frame_edicoes, text="Nova Força:", anchor="w").grid(row=0, column=2, sticky="w")
    g.deducao_forca_entry = tk.Entry(frame_edicoes)
    g.deducao_forca_entry.grid(row=1, column=2, padx=5, pady=5, sticky="ew")

    tk.Button(frame_edicoes, text="Atualizar", command=editar_deducao, bg="green").grid(row=1, column=3, padx=5, pady=5)
    tk.Button(frame_edicoes, text="Excluir", command=excluir_deducao, bg="red").grid(row=1, column=4, padx=5, pady=5)

    #aviso_label = tk.Label(root, text="", font=("Helvetica", 10))
    #aviso_label.pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    main(None)
