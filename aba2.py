import tkinter as tk
from tkinter import ttk
import globals as g

def criar_aba2(notebook):
    aba2 = ttk.Frame(notebook)
    aba2.pack(fill='both', expand=True)
    notebook.add(aba2, text='Aba 2')

    # Conteúdo da Aba 2
    # Novo frame para entradas de valores de dobra
    frame_aba2 = tk.Frame(aba2)
    frame_aba2.pack(padx=10, pady=5)

    # Labels

    tk.Label(frame_aba2, text="Dobra 1:").grid(row=1, column=0, padx=5, pady=5)
    tk.Label(frame_aba2, text="Dobra 2:").grid(row=2, column=0, padx=5, pady=5)
    tk.Label(frame_aba2, text="Dobra 3:").grid(row=3, column=0, padx=5, pady=5)
    tk.Label(frame_aba2, text="Dobra 4:").grid(row=4, column=0, padx=5, pady=5)
    tk.Label(frame_aba2, text="Dobra 5:").grid(row=5, column=0, padx=5, pady=5)

    # Entradas para inserir distancia
    tk.Label(frame_aba2, text="Distancia:").grid(row=0, column=1, padx=5, pady=5)

    g.dist1_entry = tk.Entry(frame_aba2)
    g.dist1_entry.grid(row=1, column=1, padx=5, pady=5)
    g.dist2_entry = tk.Entry(frame_aba2)
    g.dist2_entry.grid(row=2, column=1, padx=5, pady=5)
    g.dist3_entry = tk.Entry(frame_aba2)
    g.dist3_entry.grid(row=3, column=1, padx=5, pady=5)
    g.dist4_entry = tk.Entry(frame_aba2)
    g.dist4_entry.grid(row=4, column=1, padx=5, pady=5)
    g.dist5_entry = tk.Entry(frame_aba2)
    g.dist5_entry.grid(row=5, column=1, padx=5, pady=5)

    # Medida da linha de dobra
    tk.Label(frame_aba2, text="Ângulo:").grid(row=0, column=2, padx=5, pady=5)

    g.angulo1_entry = tk.Entry(frame_aba2)
    g.angulo1_entry.grid(row=1, column=2, padx=5, pady=5)
    g.angulo2_entry = tk.Entry(frame_aba2)
    g.angulo2_entry.grid(row=2, column=2, padx=5, pady=5)
    g.angulo3_entry = tk.Entry(frame_aba2)
    g.angulo3_entry.grid(row=3, column=2, padx=5, pady=5)
    g.angulo4_entry = tk.Entry(frame_aba2)
    g.angulo4_entry.grid(row=4, column=2, padx=5, pady=5)
    g.angulo5_entry = tk.Entry(frame_aba2)
    g.angulo5_entry.grid(row=5, column=2, padx=5, pady=5)

    # Medida da linha de dobra
    tk.Label(frame_aba2, text="Medida dobra:").grid(row=0, column=3, padx=5, pady=5)
    
    g.linha_dobra1_entry = tk.Entry(frame_aba2, state='readonly')
    g.linha_dobra1_entry.grid(row=1, column=3, padx=5, pady=5)
    g.linha_dobra2_entry = tk.Entry(frame_aba2, state='readonly')
    g.linha_dobra2_entry.grid(row=2, column=3, padx=5, pady=5)
    g.linha_dobra3_entry = tk.Entry(frame_aba2, state='readonly')
    g.linha_dobra3_entry.grid(row=3, column=3, padx=5, pady=5)
    g.linha_dobra4_entry = tk.Entry(frame_aba2, state='readonly')
    g.linha_dobra4_entry.grid(row=4, column=3, padx=5, pady=5)
    g.linha_dobra5_entry = tk.Entry(frame_aba2, state='readonly')
    g.linha_dobra5_entry.grid(row=5, column=3, padx=5, pady=5)
    
