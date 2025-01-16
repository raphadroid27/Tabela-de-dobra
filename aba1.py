import tkinter as tk
from tkinter import ttk
from models import espessura, material, canal, deducao
from head import *
import globals as g
from funcoes import *

def criar_aba1(notebook):
    
    # Layout
    aba1 = ttk.Frame(notebook, width=400, height=400)
    aba1.pack(fill='both', expand=True)
    notebook.add(aba1, text='Aba 1')

    # Frame para dedução específica, aba mínimo externa e Altura mín. ext. Z 90°	


    frame_superior = tk.Frame(aba1)
    frame_superior.pack(padx=10, pady=10)

    deducao_espec_label = tk.Label(frame_superior, text="Dedução Específica:")
    deducao_espec_label.grid(row=0, column=0, padx=5, pady=5)

    g.deducao_espec_entry = tk.Entry(frame_superior)
    g.deducao_espec_entry.grid(row=1, column=0, padx=5, pady=5)

    aba_min_externa_label = tk.Label(frame_superior, text="Aba Mínima Externa:")
    aba_min_externa_label.grid(row=0, column=1, padx=5, pady=5)

    g.aba_min_externa_entry = tk.Entry(frame_superior, state='readonly')
    g.aba_min_externa_entry.grid(row=1, column=1, padx=5, pady=5)

    altura_min_externa_label = tk.Label(frame_superior, text="Altura Mínima Externa Z 90°:")
    altura_min_externa_label.grid(row=0, column=2, padx=5, pady=5)

    g.altura_min_externa_entry = tk.Entry(frame_superior, state='readonly')
    g.altura_min_externa_entry.grid(row=1, column=2, padx=5, pady=5)

    # Novo frame para entradas de valores de dobra
    frame_dobras = tk.Frame(aba1)
    frame_dobras.pack(padx=10, pady=10)

    # Labels para as entradas de valores de dobra
    tk.Label(frame_dobras, text="Dobra 1:").grid(row=0, column=0, padx=5, pady=5)
    aba2_label = tk.Label(frame_dobras, text="Dobra 2:")
    aba2_label.grid(row=1, column=0, padx=5, pady=5)
    dobra3_label = tk.Label(frame_dobras, text="Dobra 3:")
    dobra3_label.grid(row=2, column=0, padx=5, pady=5)
    dobra4_label = tk.Label(frame_dobras, text="Dobra 4:")
    dobra4_label.grid(row=3, column=0, padx=5, pady=5)
    dobra5_label = tk.Label(frame_dobras, text="Dobra 5:")
    dobra5_label.grid(row=4, column=0, padx=5, pady=5)

    # Entradas para inserir valores de dobra
    g.dobra1 = tk.Entry(frame_dobras)
    g.dobra1.grid(row=0, column=1, padx=5, pady=5)
    g.dobra2 = tk.Entry(frame_dobras)
    g.dobra2.grid(row=1, column=1, padx=5, pady=5)
    g.dobra3 = tk.Entry(frame_dobras)
    g.dobra3.grid(row=2, column=1, padx=5, pady=5)
    g.dobra4 = tk.Entry(frame_dobras)
    g.dobra4.grid(row=3, column=1, padx=5, pady=5)
    g.dobra5 = tk.Entry(frame_dobras)
    g.dobra5.grid(row=4, column=1, padx=5, pady=5)

    # Medida da linha de dobra
    g.medidadobra1_entry = tk.Entry(frame_dobras, state='readonly')
    g.medidadobra1_entry.grid(row=0, column=2, padx=5, pady=5)
    g.medidadobra2_entry = tk.Entry(frame_dobras, state='readonly')
    g.medidadobra2_entry.grid(row=1, column=2, padx=5, pady=5)
    g.medidadobra3_entry = tk.Entry(frame_dobras, state='readonly')
    g.medidadobra3_entry.grid(row=2, column=2, padx=5, pady=5)
    g.medidadobra4_entry = tk.Entry(frame_dobras, state='readonly')
    g.medidadobra4_entry.grid(row=3, column=2, padx=5, pady=5)
    g.medidadobra5_entry = tk.Entry(frame_dobras, state='readonly')
    g.medidadobra5_entry.grid(row=4, column=2, padx=5, pady=5)

    # Medida da linha de dobra
    g.metadedobra1_entry = tk.Entry(frame_dobras, state='readonly')
    g.metadedobra1_entry.grid(row=0, column=3, padx=5, pady=5)
    g.metadedobra2_entry = tk.Entry(frame_dobras, state='readonly')
    g.metadedobra2_entry.grid(row=1, column=3, padx=5, pady=5)
    g.metadedobra3_entry = tk.Entry(frame_dobras, state='readonly')
    g.metadedobra3_entry.grid(row=2, column=3, padx=5, pady=5)
    g.metadedobra4_entry = tk.Entry(frame_dobras, state='readonly')
    g.metadedobra4_entry.grid(row=3, column=3, padx=5, pady=5)
    g.metadedobra5_entry = tk.Entry(frame_dobras, state='readonly')
    g.metadedobra5_entry.grid(row=4, column=3, padx=5, pady=5)

    # Botão para limpar valores de dobras
    limpar_dobras_button = tk.Button(aba1, text="Limpar Dobras", command=limpar_dobras)
    limpar_dobras_button.pack(pady=10)
    # Botão para limpar todos os valores
    limpar_tudo_button = tk.Button(aba1, text="Limpar Tudo", command=limpar_tudo)
    limpar_tudo_button.pack(pady=10)

    g.deducao_entry.bind("<KeyRelease>", lambda event: todas_funcoes())

    g.deducao_espec_entry.bind("<KeyRelease>", lambda event: todas_funcoes())
    g.dobra1.bind("<KeyRelease>", lambda event: todas_funcoes())
    g.dobra2.bind("<KeyRelease>", lambda event: todas_funcoes())
    g.dobra3.bind("<KeyRelease>", lambda event: todas_funcoes())
    g.dobra4.bind("<KeyRelease>", lambda event: todas_funcoes())
    g.dobra5.bind("<KeyRelease>", lambda event: todas_funcoes())

    g.canal_combobox.bind("<<ComboboxSelected>>", lambda event: todas_funcoes())
    g.espessura_combobox.bind("<<ComboboxSelected>>", lambda event: todas_funcoes())
    g.material_combobox.bind("<<ComboboxSelected>>", lambda event: todas_funcoes())
    g.raio_interno_valor.bind("<KeyRelease>", lambda event: todas_funcoes())