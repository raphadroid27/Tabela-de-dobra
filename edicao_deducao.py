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

    # Posicionar a janela nova_deducao em relação à janela principal
    #root.update_idletasks() 
   # x = root_app.winfo_x() + root_app.winfo_width() + 10
   # y = root_app.winfo_y()
   # root.geometry(f"+{x}+{y}")

    main_frame = tk.Frame(root)
    main_frame.pack(pady=5, padx=5)

    frame_busca = tk.LabelFrame(main_frame, text='Filtrar Deduções', pady=5)
    frame_busca.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

    frame_busca.columnconfigure(0, weight=2)
    frame_busca.columnconfigure(1, weight=2)
    frame_busca.columnconfigure(2, weight=2)
    frame_busca.columnconfigure(3, weight=1)

    tk.Label(frame_busca, text="Material:").grid(row=0, column=0, padx=2, sticky='sw')
    g.busca_material_combobox = ttk.Combobox(frame_busca, values=[m.nome for m in session.query(material).all()])
    g.busca_material_combobox.grid(row=1, column=0, padx=5, sticky="ew")

    tk.Label(frame_busca, text="Espessura:").grid(row=0, column=1, padx=2, sticky='sw')
    g.busca_espessura_combobox = ttk.Combobox(frame_busca, values=[e.valor for e in session.query(espessura).all()])
    g.busca_espessura_combobox.grid(row=1, column=1, padx=5, sticky="ew")

    tk.Label(frame_busca, text="Canal:").grid(row=0, column=2, padx=2, sticky='sw')
    g.busca_canal_combobox = ttk.Combobox(frame_busca, values=[c.valor for c in session.query(canal).all()])
    g.busca_canal_combobox.grid(row=1, column=2, padx=5, sticky="ew")

    tk.Button(frame_busca, text="Buscar", command=buscar_deducoes).grid(row=1, column=3, padx=5, pady=5)
    tk.Button(frame_busca, text="Limpar", command=limpar_busca_deducao).grid(row=1, column=4, padx=5, pady=5)

    columns = ("Material", "Espessura","Canal", "Dedução", "Observação", "Força")
    g.tree = ttk.Treeview(main_frame, columns=columns, show="headings")
    for col in columns:
        g.tree.heading(col, text=col)
        g.tree.column(col, anchor="center", width=60)
        g.tree.column("Material", width=80)
        g.tree.column("Observação", width=120, anchor="w")

    g.tree.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

    tk.Button(main_frame, text="Excluir", command=excluir_deducao, bg="red").grid(row=2, column=0, padx=5, pady=5,sticky="e")

    carregar_deducoes()

    frame_edicoes = tk.LabelFrame(main_frame, text='Editar Dedução', pady=5)
    frame_edicoes.grid(row=3, column=0, padx=5, pady=5, sticky="ew")

    frame_edicoes.columnconfigure(0, weight=2)
    frame_edicoes.columnconfigure(1, weight=2)
    frame_edicoes.columnconfigure(2, weight=2)
    frame_edicoes.columnconfigure(3, weight=1)

    tk.Label(frame_edicoes, text="Dedução:").grid(row=0, column=0, padx=2, sticky='sw')
    g.deducao_valor_entry = tk.Entry(frame_edicoes)
    g.deducao_valor_entry.grid(row=1, column=0, padx=5, sticky="ew")

    tk.Label(frame_edicoes, text="Observação:").grid(row=0, column=1,padx=2, sticky='sw')
    g.deducao_obs_entry = tk.Entry(frame_edicoes)
    g.deducao_obs_entry.grid(row=1, column=1, padx=5, sticky="ew")

    tk.Label(frame_edicoes, text="Força:").grid(row=0, padx=2, column=2, sticky='sw')
    g.deducao_forca_entry = tk.Entry(frame_edicoes)
    g.deducao_forca_entry.grid(row=1, column=2, padx=5, sticky="ew")

    tk.Button(frame_edicoes, text="Atualizar", command=editar_deducao, bg="green").grid(row=1, column=3, padx=5, pady=5, sticky="eW")

    root.mainloop()

if __name__ == "__main__":
    main(None)
