import tkinter as tk
from tkinter import ttk
import globals as g
from funcoes import *

# Configuração do banco de dados
engine = create_engine('sqlite:///tabela_de_dobra.db')
Session = sessionmaker(bind=engine)
session = Session()

def dados_dobra(root):
    dobra = ttk.Frame(root)
    dobra.pack(padx=10, fill='both', expand=True)

    # Novo frame para entradas de valores de dobra
    frame_dobra = tk.Frame(dobra)
    frame_dobra.pack(fill='both', expand=True, pady=5)

    frame_dobra.columnconfigure(0, weight=1)
    frame_dobra.columnconfigure(1, weight=1)
    frame_dobra.columnconfigure(2, weight=1)
    frame_dobra.columnconfigure(3, weight=1)

    tk.Label(frame_dobra, text="Medida Ext.:").grid(row=0, column=1)
    tk.Label(frame_dobra, text="Medida Dobra:").grid(row=0, column=2)
    tk.Label(frame_dobra, text="Metade Dobra:").grid(row=0, column=3)
    
    frame_dobra.rowconfigure(0, weight=0)

    def dobras(valor):
        g.n = valor

        # Remover widgets existentes
        for widget in frame_dobra.winfo_children():
            widget.destroy()

        # Adicionar widgets novamente
        tk.Label(frame_dobra, text="Medida Ext.:").grid(row=0, column=1)
        tk.Label(frame_dobra, text="Medida Dobra:").grid(row=0, column=2)
        tk.Label(frame_dobra, text="Metade Dobra:").grid(row=0, column=3)

        for i in range(1, g.n):
            frame_dobra.rowconfigure(i, weight=0)

            tk.Label(frame_dobra, text=f"Aba {i}:").grid(row=i, column=0)

            setattr(g, f'aba{i}_entry', tk.Entry(frame_dobra, width=10))
            getattr(g, f'aba{i}_entry').grid(row=i, column=1, sticky='we', padx=2)
            getattr(g, f'aba{i}_entry').bind("<KeyRelease>", lambda event: calcular_dobra())

            setattr(g, f'medidadobra{i}_label', tk.Label(frame_dobra, relief="sunken", width=10))
            getattr(g, f'medidadobra{i}_label').grid(row=i, column=2, sticky='we', padx=2)
            getattr(g, f'medidadobra{i}_label').bind("<Button-1>", lambda event, i=i: copiar('medida_dobra',i))

            setattr(g, f'metadedobra{i}_label', tk.Label(frame_dobra, relief="sunken", width=10))
            getattr(g, f'metadedobra{i}_label').grid(row=i, column=3, sticky='we', padx=2)
            getattr(g, f'metadedobra{i}_label').bind("<Button-1>", lambda event, i=i: copiar('metade_dobra',i))

    dobras(g.n)

    frame_inferior = tk.Frame(dobra)
    frame_inferior.pack(fill='both', expand=True)
    
    tk.Button(frame_inferior, text="+", command=lambda: dobras(11)).pack(side='right')
    tk.Button(frame_inferior, text="-", command=lambda: dobras(6)).pack(side='right')
    
    tk.Label(frame_inferior, text="Medida do Blank:").pack(side='left')
    g.medida_blank_label = tk.Label(frame_inferior, relief="sunken", width=10)
    g.medida_blank_label.pack(side='left')
    g.medida_blank_label.bind("<Button-1>", lambda event: copiar('blank'))

    g.metade_blank_label = tk.Label(frame_inferior, relief="sunken", width=10)
    g.metade_blank_label.pack(side='left')
    g.metade_blank_label.bind("<Button-1>", lambda event: copiar('metade_blank'))