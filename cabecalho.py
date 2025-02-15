import tkinter as tk
from tkinter import ttk
from models import espessura, material, canal, deducao
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import globals as g
from funcoes import *

# Configuração do banco de dados
engine = create_engine('sqlite:///tabela_de_dobra.db')
Session = sessionmaker(bind=engine)
session = Session()

def cabecalho(root):
    cabecalho = ttk.Frame(root)
    cabecalho.pack(padx=10, fill='both', expand=True)

    # Primeira linha frame
    input_frame = tk.Frame(cabecalho)
    input_frame.pack(fill='both', expand=True)

    input_frame.columnconfigure(0, weight=1)
    input_frame.columnconfigure(1, weight=1)
    input_frame.columnconfigure(2, weight=1)
    input_frame.columnconfigure(3, weight=1)

    tk.Label(input_frame, text="Material:").grid(row=0, column=0, sticky='sw')

    g.material_combobox = ttk.Combobox(input_frame, width=10,justify="center")
    g.material_combobox.grid(row=1, column=0, padx=2, sticky='we')

    tk.Label(input_frame, text="Espessura:").grid(row=0, column=1, sticky='sw')

    g.espessura_combobox = ttk.Combobox(input_frame, width=10,justify="center")
    g.espessura_combobox.grid(row=1, column=1, padx=2, sticky='we')

    tk.Label(input_frame, text="Canal:").grid(row=0, column=2, sticky='sw')

    g.canal_combobox = ttk.Combobox(input_frame, width=10,justify="center")
    g.canal_combobox.grid(row=1, column=2, padx=2, sticky='we')

    tk.Label(input_frame, text="Comprimento:").grid(row=0, column=3, sticky='sw')

    g.comprimento_entry = tk.Entry(input_frame, width=10, justify="center")
    g.comprimento_entry.grid(row=1, column=3, padx=2, sticky='we')

    # Segunda linha frame
    results_frame = tk.Frame(cabecalho)
    results_frame.pack(fill='both', expand=True)

    # Configurar a largura das colunas do grid
    results_frame.columnconfigure(0, weight=1)
    results_frame.columnconfigure(1, weight=1)
    results_frame.columnconfigure(2, weight=1)
    results_frame.columnconfigure(3, weight=1)

    # Raio interno
    tk.Label(results_frame, text="Raio Int.:").grid(row=0, column=0, sticky='sw')

    g.raio_interno_entry = tk.Entry(results_frame, width=10, justify="center")
    g.raio_interno_entry.grid(row=1, column=0, padx=2, sticky='we')

    # Fator K
    tk.Label(results_frame, text="Fator K:").grid(row=0, column=1, sticky='sw')

    g.fator_k_label = tk.Label(results_frame, relief="sunken", width=10)
    g.fator_k_label.grid(row=1, column=1, padx=2, sticky='we')
    g.fator_k_label.bind("<Button-1>", lambda event: copiar_fatork())

    # Dedução
    tk.Label(results_frame, text="Dedução:").grid(row=0, column=2, sticky='sw')

    g.deducao_label = tk.Label(results_frame, relief="sunken", width=10)
    g.deducao_label.grid(row=1, column=2, padx=2, sticky='we')
    g.deducao_label.bind("<Button-1>", lambda event: copiar_deducao())

    # Offset
    tk.Label(results_frame, text="Offset:").grid(row=0, column=3, sticky='sw')

    g.offset_label = tk.Label(results_frame, relief="sunken", width=10)
    g.offset_label.grid(row=1, column=3, padx=2, sticky='we')
    g.offset_label.bind("<Button-1>", lambda event: copiar_offset())

    # Frame para dedução específica, aba mínimo externa e Altura mín. ext. Z 90°	

    frame_superior = tk.Frame(cabecalho)
    frame_superior.pack(fill='both', expand=True)

    frame_superior.columnconfigure(0, weight=1)
    frame_superior.columnconfigure(1, weight=1)
    frame_superior.columnconfigure(2, weight=1)
    frame_superior.columnconfigure(3, weight=1)

    tk.Label(frame_superior, text="Ded. Espec.:").grid(row=0, column=0, sticky='sw')

    g.deducao_espec_entry = tk.Entry(frame_superior, width=10, fg="red", justify="center")
    g.deducao_espec_entry.grid(row=1, column=0, padx=2, sticky='we')

    tk.Label(frame_superior, text="Aba Mín.:").grid(row=0, column=1, sticky='sw')

    g.aba_min_externa_label = tk.Label(frame_superior, relief="sunken", width=10)
    g.aba_min_externa_label.grid(row=1, column=1, padx=2, sticky='we')

    tk.Label(frame_superior, text="Mín. Ext. Z90°:").grid(row=0, column=2, sticky='sw')

    g.z_min_externa_label = tk.Label(frame_superior, relief="sunken", width=10)
    g.z_min_externa_label.grid(row=1, column=2, padx=2, sticky='we')

    tk.Label(frame_superior, text="Ton/m:").grid(row=0, column=3, sticky='sw')

    g.ton_m_label = tk.Label(frame_superior, relief="sunken", width=10)
    g.ton_m_label.grid(row=1, column=3, padx=2, sticky='we')

    #Observações
    g.obs_label = tk.Label(cabecalho, text="Observações:", relief="sunken", anchor='w')
    g.obs_label.pack(side='top', fill='x', expand=True, padx=2)

    atualizar_material()