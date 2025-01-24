import tkinter as tk
from tkinter import ttk
import globals as g
from funcoes import *

def criar_aba1(notebook):
    
    # Layout
    aba1 = ttk.Frame(notebook)
    aba1.pack(fill='both', expand=True)
    notebook.add(aba1, text='Aba 1')

    # Frame para dedução específica, aba mínimo externa e Altura mín. ext. Z 90°	

    frame_superior = tk.Frame(aba1)
    frame_superior.pack(fill='both', expand=True,anchor='n')

    frame_superior.columnconfigure(0, weight=1)
    frame_superior.columnconfigure(1, weight=1)
    frame_superior.columnconfigure(2, weight=1)

    tk.Label(frame_superior, text="Dedução Específica:").grid(row=0, column=0, padx=2)

    g.deducao_espec_entry = tk.Entry(frame_superior, width=10)
    g.deducao_espec_entry.grid(row=1, column=0, padx=2, sticky='we')

    tk.Label(frame_superior, text="Aba Mínima Externa:").grid(row=0, column=1, padx=2)

    g.aba_min_externa_entry = tk.Label(frame_superior, relief="sunken", width=10)
    g.aba_min_externa_entry.grid(row=1, column=1, padx=2, sticky='we')

    tk.Label(frame_superior, text="Altura Mín. Ext. Z 90°:").grid(row=0, column=2, padx=2)

    g.altura_min_externa_entry = tk.Label(frame_superior, relief="sunken", width=10)
    g.altura_min_externa_entry.grid(row=1, column=2, padx=2, sticky='we')

    # Novo frame para entradas de valores de dobra
    frame_aba1 = tk.Frame(aba1)
    frame_aba1.pack(fill='both', expand=True)

    frame_aba1.columnconfigure(0, weight=1)
    frame_aba1.columnconfigure(1, weight=2)
    frame_aba1.columnconfigure(2, weight=2)
    frame_aba1.columnconfigure(3, weight=2)

    tk.Label(frame_aba1, text="Medida da aba:").grid(row=0, column=1)
    tk.Label(frame_aba1, text="Medida da dobra:").grid(row=0, column=2)
    tk.Label(frame_aba1, text="Metade da dobra:").grid(row=0, column=3)


    # Labels para as entradas de valores de dobra
    tk.Label(frame_aba1, text="Aba 1:").grid(row=1, column=0)
    tk.Label(frame_aba1, text="Aba 2:").grid(row=2, column=0)
    tk.Label(frame_aba1, text="Aba 3:").grid(row=3, column=0)
    tk.Label(frame_aba1, text="Aba 4:").grid(row=4, column=0)
    tk.Label(frame_aba1, text="Aba 5:").grid(row=5, column=0)

    # Entradas para inserir valores de dobra
    g.aba1_entry = tk.Entry(frame_aba1, width=10)
    g.aba1_entry.grid(row=1, column=1, sticky='we',padx=2)
    g.aba2_entry = tk.Entry(frame_aba1, width=10)
    g.aba2_entry.grid(row=2, column=1, sticky='we',padx=2)
    g.aba3_entry = tk.Entry(frame_aba1, width=10)
    g.aba3_entry.grid(row=3, column=1, sticky='we',padx=2)
    g.aba4_entry = tk.Entry(frame_aba1, width=10)
    g.aba4_entry.grid(row=4, column=1, sticky='we',padx=2)
    g.aba5_entry = tk.Entry(frame_aba1, width=10)
    g.aba5_entry.grid(row=5, column=1, sticky='we',padx=2)

    # Medida da linha de dobra
    g.medidadobra1_entry = tk.Label(frame_aba1,relief="sunken", width=10)
    g.medidadobra1_entry.grid(row=1, column=2, sticky='we',padx=2)
    g.medidadobra2_entry = tk.Label(frame_aba1, relief="sunken", width=10)
    g.medidadobra2_entry.grid(row=2, column=2, sticky='we',padx=2)
    g.medidadobra3_entry = tk.Label(frame_aba1, relief="sunken", width=10)
    g.medidadobra3_entry.grid(row=3, column=2, sticky='we',padx=2)
    g.medidadobra4_entry = tk.Label(frame_aba1, relief="sunken", width=10)
    g.medidadobra4_entry.grid(row=4, column=2, sticky='we',padx=2)
    g.medidadobra5_entry = tk.Label(frame_aba1, relief="sunken", width=10)
    g.medidadobra5_entry.grid(row=5, column=2, sticky='we',padx=2)

    # Medida da linha de dobra
    g.metadedobra1_entry = tk.Label(frame_aba1,relief="sunken", width=10)
    g.metadedobra1_entry.grid(row=1, column=3, sticky='we',padx=2)
    g.metadedobra2_entry = tk.Label(frame_aba1,relief="sunken", width=10)
    g.metadedobra2_entry.grid(row=2, column=3, sticky='we',padx=2)
    g.metadedobra3_entry = tk.Label(frame_aba1,relief="sunken", width=10)
    g.metadedobra3_entry.grid(row=3, column=3, sticky='we',padx=2)
    g.metadedobra4_entry = tk.Label(frame_aba1,relief="sunken", width=10)
    g.metadedobra4_entry.grid(row=4, column=3, sticky='we',padx=2)
    g.metadedobra5_entry = tk.Label(frame_aba1,relief="sunken", width=10)
    g.metadedobra5_entry.grid(row=5, column=3, sticky='we',padx=2)

    tk.Label(frame_aba1, text="Medida do Blank:").grid(row=6, column=1, padx=2, sticky='e')
    
    g.medida_blank_label = tk.Label(frame_aba1, relief="sunken", width=10)
    g.medida_blank_label.grid(row=6, column=2, sticky='we',padx=2)

    # Botão para limpar valores de dobras
    limpar_dobras_button = tk.Button(frame_aba1, text="Limpar Dobras", command=limpar_dobras, bg='yellow')
    limpar_dobras_button.grid(row=6, column=3, sticky='we',padx=2)