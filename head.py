import tkinter as tk
from tkinter import ttk
from models import espessura, material, canal, deducao
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import globals as g
from funcoes import *

def cabecalho(root):
    session = configuracao_do_banco_de_dados()

    cabecalho = ttk.Frame(root)
    cabecalho.place(x=15, y=0, width=400, height=80)

    # Primeira linha frame
    input_frame = tk.Frame(cabecalho)
    input_frame.pack(padx=0, pady=0, fill='x', expand=True)

    input_frame.columnconfigure(0, weight=1)
    input_frame.columnconfigure(1, weight=1)
    input_frame.columnconfigure(2, weight=1)

    tk.Label(input_frame, text="Material:").grid(row=0, column=0, sticky='w')

    g.material_combobox = ttk.Combobox(input_frame, values=[m.nome for m in session.query(material).all()])
    g.material_combobox.grid(row=1, column=0, padx=5, sticky='ew')

    tk.Label(input_frame, text="Espessura: ").grid(row=0, column=1, sticky='ew')

    g.espessura_combobox = ttk.Combobox(input_frame)
    g.espessura_combobox.grid(row=1, column=1, padx=5, sticky='ew')

    tk.Label(input_frame, text="Canal:").grid(row=0, column=2, sticky='ew')

    g.canal_combobox = ttk.Combobox(input_frame)
    g.canal_combobox.grid(row=1, column=2, padx=5, sticky='ew')

    # Segunda linha frame
    results_frame = tk.Frame(cabecalho)
    results_frame.pack(padx=0, pady=0, fill='x', expand=True)

    # Configurar a largura das colunas do grid
    results_frame.columnconfigure(0, weight=1)
    results_frame.columnconfigure(1, weight=1)
    results_frame.columnconfigure(2, weight=1)
    results_frame.columnconfigure(3, weight=1)

    # Raio interno
    raio_interno_label = tk.Label(results_frame, text="Raio Interno: ")
    raio_interno_label.grid(row=0, column=0, padx=5, sticky='ew')

    g.raio_interno_entry = tk.Entry(results_frame)
    g.raio_interno_entry.grid(row=1, column=0, padx=5, sticky='ew')

    # Fator K
    fator_k_label = tk.Label(results_frame, text="Fator K: ")
    fator_k_label.grid(row=0, column=1, padx=5, sticky='ew')

    g.fator_k_entry = tk.Entry(results_frame, state='readonly')
    g.fator_k_entry.grid(row=1, column=1, padx=5, sticky='ew')

    # Dedução
    deducao_label = tk.Label(results_frame, text="Dedução: ")
    deducao_label.grid(row=0, column=2, padx=5, sticky='ew')

    g.deducao_entry = tk.Entry(results_frame, state='readonly')
    g.deducao_entry.grid(row=1, column=2, padx=5, sticky='ew')

    # Offset
    offset_label = tk.Label(results_frame, text="Offset: ")
    offset_label.grid(row=0, column=3, padx=5, sticky='ew')

    g.offset_entry = tk.Entry(results_frame, state='readonly')
    g.offset_entry.grid(row=1, column=3, padx=5, sticky='ew')