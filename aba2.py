import tkinter as tk
from tkinter import ttk
import globals as g

def criar_aba2(notebook):
    aba2 = ttk.Frame(notebook)
    aba2.pack(fill='both', expand=True)
    notebook.add(aba2, text='Aba 2')

    # Frame para entradas de valores de dobra
    frame_aba2 = tk.Frame(aba2)
    frame_aba2.pack(fill='both', expand=True, pady=5)

    frame_aba2.columnconfigure(0, weight=1)
    frame_aba2.columnconfigure(1, weight=2)
    frame_aba2.columnconfigure(2, weight=2)
    frame_aba2.columnconfigure(3, weight=2)

    tk.Label(frame_aba2, text="Distância:").grid(row=0, column=1)
    tk.Label(frame_aba2, text="Ângulo:").grid(row=0, column=2)
    tk.Label(frame_aba2, text="Medida Dobra:").grid(row=0, column=3)

    # Labels para as entradas de valores de dobra
    tk.Label(frame_aba2, text="Dobra 1:").grid(row=1, column=0)
    tk.Label(frame_aba2, text="Dobra 2:").grid(row=2, column=0)
    tk.Label(frame_aba2, text="Dobra 3:").grid(row=3, column=0)
    tk.Label(frame_aba2, text="Dobra 4:").grid(row=4, column=0)
    tk.Label(frame_aba2, text="Dobra 5:").grid(row=5, column=0)

    # Entradas para inserir valores de dobra
    g.dist1_entry = tk.Entry(frame_aba2, width=10)
    g.dist1_entry.grid(row=1, column=1, sticky='we', padx=2)
    g.dist2_entry = tk.Entry(frame_aba2, width=10)
    g.dist2_entry.grid(row=2, column=1, sticky='we', padx=2)
    g.dist3_entry = tk.Entry(frame_aba2, width=10)
    g.dist3_entry.grid(row=3, column=1, sticky='we', padx=2)
    g.dist4_entry = tk.Entry(frame_aba2, width=10)
    g.dist4_entry.grid(row=4, column=1, sticky='we', padx=2)
    g.dist5_entry = tk.Entry(frame_aba2, width=10)
    g.dist5_entry.grid(row=5, column=1, sticky='we', padx=2)

    g.angulo1_entry = tk.Entry(frame_aba2, width=10)
    g.angulo1_entry.grid(row=1, column=2, sticky='we', padx=2)
    g.angulo2_entry = tk.Entry(frame_aba2, width=10)
    g.angulo2_entry.grid(row=2, column=2, sticky='we', padx=2)
    g.angulo3_entry = tk.Entry(frame_aba2, width=10)
    g.angulo3_entry.grid(row=3, column=2, sticky='we', padx=2)
    g.angulo4_entry = tk.Entry(frame_aba2, width=10)
    g.angulo4_entry.grid(row=4, column=2, sticky='we', padx=2)
    g.angulo5_entry = tk.Entry(frame_aba2, width=10)
    g.angulo5_entry.grid(row=5, column=2, sticky='we', padx=2)

    g.linha_dobra1_label = tk.Label(frame_aba2, relief="sunken", width=10)
    g.linha_dobra1_label.grid(row=1, column=3, sticky='we', padx=2)
    g.linha_dobra2_label = tk.Label(frame_aba2, relief="sunken", width=10)
    g.linha_dobra2_label.grid(row=2, column=3, sticky='we', padx=2)
    g.linha_dobra3_label = tk.Label(frame_aba2, relief="sunken", width=10)
    g.linha_dobra3_label.grid(row=3, column=3, sticky='we', padx=2)
    g.linha_dobra4_label = tk.Label(frame_aba2, relief="sunken", width=10)
    g.linha_dobra4_label.grid(row=4, column=3, sticky='we', padx=2)
    g.linha_dobra5_label = tk.Label(frame_aba2, relief="sunken", width=10)
    g.linha_dobra5_label.grid(row=5, column=3, sticky='we', padx=2)

    # Label e campo para a soma da terceira coluna
    tk.Label(frame_aba2, text="Soma:").grid(row=6, column=2, sticky='e', padx=2)
    g.soma_linha_dobra_label = tk.Label(frame_aba2, relief="sunken", width=10)
    g.soma_linha_dobra_label.grid(row=6, column=3, sticky='we', padx=2)