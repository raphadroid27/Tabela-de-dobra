import tkinter as tk
from tkinter import ttk
import globals as g
from funcoes import *

def criar_aba1(notebook):
    # Layout
    aba1 = ttk.Frame(notebook)
    aba1.pack(fill='both', expand=True)
    notebook.add(aba1, text='Cálculo de dobra 90°')

    # Novo frame para entradas de valores de dobra
    frame_aba1 = tk.Frame(aba1)
    frame_aba1.pack(fill='both', expand=True, pady=5)

    frame_aba1.columnconfigure(0, weight=1)
    frame_aba1.columnconfigure(1, weight=2)
    frame_aba1.columnconfigure(2, weight=2)
    frame_aba1.columnconfigure(3, weight=2)

    frame_aba1.rowconfigure(0,weight=1)
    frame_aba1.rowconfigure(1,weight=1)
    frame_aba1.rowconfigure(2,weight=1)
    frame_aba1.rowconfigure(3,weight=1)
    frame_aba1.rowconfigure(4,weight=1)
    frame_aba1.rowconfigure(5,weight=1)

    
    tk.Label(frame_aba1, text="Medida Ext.:").grid(row=0, column=1)
    tk.Label(frame_aba1, text="Medida Dobra:").grid(row=0, column=2)
    tk.Label(frame_aba1, text="Metade Dobra:").grid(row=0, column=3)


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
    g.medidadobra1_label = tk.Label(frame_aba1,relief="sunken", width=10)
    g.medidadobra1_label.grid(row=1, column=2, sticky='we',padx=2)
    g.medidadobra2_label = tk.Label(frame_aba1, relief="sunken", width=10)
    g.medidadobra2_label.grid(row=2, column=2, sticky='we',padx=2)
    g.medidadobra3_label = tk.Label(frame_aba1, relief="sunken", width=10)
    g.medidadobra3_label.grid(row=3, column=2, sticky='we',padx=2)
    g.medidadobra4_label = tk.Label(frame_aba1, relief="sunken", width=10)
    g.medidadobra4_label.grid(row=4, column=2, sticky='we',padx=2)
    g.medidadobra5_label = tk.Label(frame_aba1, relief="sunken", width=10)
    g.medidadobra5_label.grid(row=5, column=2, sticky='we',padx=2)

    # Medida da linha de dobra
    g.metadedobra1_label = tk.Label(frame_aba1,relief="sunken", width=10)
    g.metadedobra1_label.grid(row=1, column=3, sticky='we',padx=2)
    g.metadedobra2_label = tk.Label(frame_aba1,relief="sunken", width=10)
    g.metadedobra2_label.grid(row=2, column=3, sticky='we',padx=2)
    g.metadedobra3_label = tk.Label(frame_aba1,relief="sunken", width=10)
    g.metadedobra3_label.grid(row=3, column=3, sticky='we',padx=2)
    g.metadedobra4_label = tk.Label(frame_aba1,relief="sunken", width=10)
    g.metadedobra4_label.grid(row=4, column=3, sticky='we',padx=2)
    g.metadedobra5_label = tk.Label(frame_aba1,relief="sunken", width=10)
    g.metadedobra5_label.grid(row=5, column=3, sticky='we',padx=2)

    tk.Label(frame_aba1, text="Medida do Blank:").grid(row=6, column=0,columnspan=2,sticky='e',padx=2)
    
    g.medida_blank_label = tk.Label(frame_aba1, relief="sunken", width=10)
    g.medida_blank_label.grid(row=6, column=2, sticky='we',padx=2)
    g.medida_blank_label.bind("<Button-1>", lambda event: copiar_blank())

    g.metade_blank_label = tk.Label(frame_aba1, relief="sunken", width=10)
    g.metade_blank_label.grid(row=6, column=3, sticky='we',padx=2)
    g.metade_blank_label.bind("<Button-1>", lambda event: copiar_metade_blank())