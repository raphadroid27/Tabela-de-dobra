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
    cabecalho.pack(padx=10,pady=10,fill='both', expand=True)

    # Primeira linha frame
    input_frame = tk.Frame(cabecalho)
    input_frame.pack(padx=0, pady=0, fill='both', expand=True)

    input_frame.columnconfigure(0, weight=1)
    input_frame.columnconfigure(1, weight=1)
    input_frame.columnconfigure(2, weight=1)

    tk.Label(input_frame, text="Material:").grid(row=0, column=0, padx=2, sticky='w')

    g.material_combobox = ttk.Combobox(input_frame, values=[m.nome for m in session.query(material).all()])
    g.material_combobox.grid(row=1, column=0, padx=5)

    tk.Label(input_frame, text="Espessura:").grid(row=0, column=1, padx=2, sticky='w')

    g.espessura_combobox = ttk.Combobox(input_frame)
    g.espessura_combobox.grid(row=1, column=1, padx=5)

    tk.Label(input_frame, text="Canal:").grid(row=0, column=2, padx=2, sticky='w')

    g.canal_combobox = ttk.Combobox(input_frame)
    g.canal_combobox.grid(row=1, column=2, padx=5)

    # Segunda linha frame
    results_frame = tk.Frame(cabecalho)
    results_frame.pack(padx=0, pady=0, fill='both', expand=True)

    # Configurar a largura das colunas do grid
    results_frame.columnconfigure(0, weight=1)
    results_frame.columnconfigure(1, weight=1)
    results_frame.columnconfigure(2, weight=1)
    results_frame.columnconfigure(3, weight=1)

    # Raio interno
    tk.Label(results_frame, text="Raio Interno:").grid(row=0, column=0, padx=2, sticky='w')

    g.raio_interno_entry = tk.Entry(results_frame)
    g.raio_interno_entry.grid(row=1, column=0, padx=5, sticky='we')

    # Fator K
    tk.Label(results_frame, text="Fator K: ").grid(row=0, column=1, padx=2, sticky='w')

    g.fator_k_entry = tk.Label(results_frame, relief="sunken")
    g.fator_k_entry.grid(row=1, column=1, padx=5, sticky='we')

    # Dedução
    tk.Label(results_frame, text="Dedução: ").grid(row=0, column=2, padx=2, sticky='w')

    g.deducao_entry = tk.Label(results_frame, relief="sunken")
    g.deducao_entry.grid(row=1, column=2, padx=5, sticky='we')

    # Offset
    tk.Label(results_frame, text="Offset: ").grid(row=0, column=3, padx=2, sticky='w')

    g.offset_entry = tk.Label(results_frame, relief="sunken")
    g.offset_entry.grid(row=1, column=3, padx=5, sticky='we')

    g.deducao_entry.bind("<Button-1>", lambda event: copiar_deducao())