import tkinter as tk
from tkinter import ttk
from models import espessura, material, canal, deducao
from head import *
import globals as g
from funcoes import *

def criar_aba1(notebook):
    
    # Layout
    aba1 = ttk.Frame(notebook)
    aba1.pack(fill='both', expand=True)
    notebook.add(aba1, text='Aba 1')

    # Frame para dedução específica, aba mínimo externa e Altura mín. ext. Z 90°	

    frame_superior = tk.Frame(aba1)
    frame_superior.pack(padx=10, pady=10)

    frame_superior.columnconfigure(0, weight=1)
    frame_superior.columnconfigure(1, weight=1)
    frame_superior.columnconfigure(2, weight=1)

    tk.Label(frame_superior, text="Dedução Específica:").grid(row=0, column=0, padx=5, pady=5)

    g.deducao_espec_entry = tk.Entry(frame_superior)
    g.deducao_espec_entry.grid(row=1, column=0, padx=5, pady=5)

    tk.Label(frame_superior, text="Aba Mínima Externa:").grid(row=0, column=1, padx=5, pady=5)

    g.aba_min_externa_entry = tk.Entry(frame_superior, state='readonly')
    g.aba_min_externa_entry.grid(row=1, column=1, padx=5, pady=5)

    altura_min_externa_label = tk.Label(frame_superior, text="Altura Mínima Externa Z 90°:")
    altura_min_externa_label.grid(row=0, column=2, padx=5, pady=5)

    g.altura_min_externa_entry = tk.Entry(frame_superior, state='readonly')
    g.altura_min_externa_entry.grid(row=1, column=2, padx=5, pady=5)

    # Novo frame para entradas de valores de dobra
    frame_aba1 = tk.Frame(aba1)
    frame_aba1.pack(fill='both', expand=True)

    frame_aba1.columnconfigure(0, weight=1, minsize=0)
    frame_aba1.columnconfigure(1, weight=1, minsize=0)
    frame_aba1.columnconfigure(2, weight=1, minsize=100)
    frame_aba1.columnconfigure(3, weight=1, minsize=100)

    # Labels para as entradas de valores de dobra
    tk.Label(frame_aba1, text="Aba 1:").grid(row=1, column=0)
    tk.Label(frame_aba1, text="Aba 2:").grid(row=2, column=0)
    tk.Label(frame_aba1, text="Aba 3:").grid(row=3, column=0)
    tk.Label(frame_aba1, text="Aba 4:").grid(row=4, column=0)
    tk.Label(frame_aba1, text="Aba 5:").grid(row=5, column=0)

    # Entradas para inserir valores de dobra
    g.aba1_entry = tk.Entry(frame_aba1)
    g.aba1_entry.grid(row=1, column=1, sticky='we',padx=5)
    g.aba2_entry = tk.Entry(frame_aba1)
    g.aba2_entry.grid(row=2, column=1, sticky='we')
    g.aba3_entry = tk.Entry(frame_aba1)
    g.aba3_entry.grid(row=3, column=1, sticky='we')
    g.aba4_entry = tk.Entry(frame_aba1)
    g.aba4_entry.grid(row=4, column=1, sticky='we')
    g.aba5_entry = tk.Entry(frame_aba1)
    g.aba5_entry.grid(row=5, column=1, sticky='we')

    # Medida da linha de dobra
    g.medidadobra1_entry = tk.Label(frame_aba1,relief="sunken")
    g.medidadobra1_entry.grid(row=1, column=2, sticky='we',padx=5)
    g.medidadobra2_entry = tk.Label(frame_aba1, relief="sunken")
    g.medidadobra2_entry.grid(row=2, column=2, sticky='we')
    g.medidadobra3_entry = tk.Label(frame_aba1, relief="sunken")
    g.medidadobra3_entry.grid(row=3, column=2, sticky='we')
    g.medidadobra4_entry = tk.Label(frame_aba1, relief="sunken")
    g.medidadobra4_entry.grid(row=4, column=2, sticky='we')
    g.medidadobra5_entry = tk.Label(frame_aba1, relief="sunken")
    g.medidadobra5_entry.grid(row=5, column=2, sticky='we')

    # Medida da linha de dobra
    g.metadedobra1_entry = tk.Label(frame_aba1,relief="sunken")
    g.metadedobra1_entry.grid(row=1, column=3, sticky='we',padx=5)
    g.metadedobra2_entry = tk.Label(frame_aba1,relief="sunken")
    g.metadedobra2_entry.grid(row=2, column=3, sticky='we')
    g.metadedobra3_entry = tk.Label(frame_aba1,relief="sunken")
    g.metadedobra3_entry.grid(row=3, column=3, sticky='we')
    g.metadedobra4_entry = tk.Label(frame_aba1,relief="sunken")
    g.metadedobra4_entry.grid(row=4, column=3, sticky='we')
    g.metadedobra5_entry = tk.Label(frame_aba1,relief="sunken")
    g.metadedobra5_entry.grid(row=5, column=3, sticky='we')
    
    g.medida_blank_label = tk.Label(frame_aba1, relief="sunken")
    g.medida_blank_label.grid(row=6, column=2, sticky='we')

    # Botão para limpar valores de dobras
    limpar_dobras_button = tk.Button(aba1, text="Limpar Dobras", command=limpar_dobras)
    limpar_dobras_button.pack(pady=10)
    # Botão para limpar todos os valores
    limpar_tudo_button = tk.Button(aba1, text="Limpar Tudo", command=limpar_tudo)
    limpar_tudo_button.pack(pady=10)

    g.deducao_entry.bind("<KeyRelease>", lambda event: todas_funcoes())

    g.deducao_espec_entry.bind("<KeyRelease>", lambda event: todas_funcoes())
    g.aba1_entry.bind("<KeyRelease>", lambda event: todas_funcoes())
    g.aba2_entry.bind("<KeyRelease>", lambda event: todas_funcoes())
    g.aba3_entry.bind("<KeyRelease>", lambda event: todas_funcoes())
    g.aba4_entry.bind("<KeyRelease>", lambda event: todas_funcoes())
    g.aba5_entry.bind("<KeyRelease>", lambda event: todas_funcoes())

    g.canal_combobox.bind("<<ComboboxSelected>>", lambda event: todas_funcoes())
    g.espessura_combobox.bind("<<ComboboxSelected>>", lambda event: todas_funcoes())
    g.material_combobox.bind("<<ComboboxSelected>>", lambda event: todas_funcoes())
    g.raio_interno_entry.bind("<KeyRelease>", lambda event: todas_funcoes())

    #funções de copiar

    g.deducao_entry.bind("<Button-1>", lambda event: copiar_deducao())
    g.fator_k_entry.bind("<Button-1>", lambda event: copiar_fatork())
    g.offset_entry.bind("<Button-1>", lambda event: copiar_offset())