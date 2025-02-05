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
    root.title("Editar/Excluir Canal")
    root.resizable(False, False)

    main_frame = tk.Frame(root)
    main_frame.pack(pady=5, padx=5, fill='both', expand=True)

    columns = ("Canal", "Largura", "Altura", "Comprimento", "Observação")
    g.lista_canal = ttk.Treeview(main_frame, columns=columns, show="headings")
    for col in columns:
        g.lista_canal.heading(col, text=col)
        g.lista_canal.column(col, anchor="center", width=20)    
    
    g.lista_canal.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

    carregar_canais()

    tk.Button(main_frame, text="Excluir", command=excluir_material, bg="red").grid(row=1, column=0, padx=5, pady=5, sticky="e")

    frame_edicoes = tk.LabelFrame(main_frame, text='Editar Canal', pady=5)
    frame_edicoes.grid(row=2, column=0, padx=5, pady=5, sticky="ew")

    frame_edicoes.columnconfigure(0, weight=1)
    frame_edicoes.columnconfigure(1, weight=1)
    frame_edicoes.columnconfigure(2, weight=1)

    tk.Label(frame_edicoes, text="Largura:", anchor="w").grid(row=0, column=0,padx=2, sticky='sw')
    g.canal_largura_entry = tk.Entry(frame_edicoes)
    g.canal_largura_entry.grid(row=1, column=0, padx=5, sticky="ew")

    tk.Label(frame_edicoes, text="Altura:", anchor="w").grid(row=0, padx=2, column=1, sticky='sw')
    g.canal_altura_entry = tk.Entry(frame_edicoes)
    g.canal_altura_entry.grid(row=1, column=1, padx=5, sticky="ew")

    tk.Label(frame_edicoes, text="Comprimento total:", anchor="w").grid(row=2, column=0, padx=2, sticky='sw')
    g.canal_comprimento_entry = tk.Entry(frame_edicoes)
    g.canal_comprimento_entry.grid(row=3, column=0, padx=5, pady=5, sticky="ew")

    tk.Label(frame_edicoes, text="Observação:", anchor="w").grid(row=2, column=1, padx=2, sticky='sw')
    g.canal_observacao_entry = tk.Entry(frame_edicoes)
    g.canal_observacao_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

    tk.Button(frame_edicoes, text="Atualizar", command=editar_canal, bg="green").grid(row=1, column=2, padx=5, pady=5, sticky="ew",rowspan=3)

    root.mainloop()

if __name__ == "__main__":
    main(None)
