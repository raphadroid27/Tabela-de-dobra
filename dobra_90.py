import tkinter as tk
from tkinter import ttk
import globals as g
from funcoes import *

# Configuração do banco de dados
engine = create_engine('sqlite:///tabela_de_dobra.db')
Session = sessionmaker(bind=engine)
session = Session()

def form_dobra(frame, w):
    g.frame_dobra = tk.Frame(frame)
    g.frame_dobra.grid(row=0, column=0, sticky='we', pady=5)

    g.frame_dobra.columnconfigure(0, weight=1)
    g.frame_dobra.columnconfigure(1, weight=1)
    g.frame_dobra.columnconfigure(2, weight=1)
    g.frame_dobra.columnconfigure(3, weight=1)
    
    dobras(g.n, w)
    return g.frame_dobra
 
def dobras(valor, w):
    # Atualizar o valor de n
    g.n = valor

    # Adicionar widgets novamente
    tk.Label(g.frame_dobra, text="Medida Ext.:").grid(row=0, column=1)
    tk.Label(g.frame_dobra, text="Medida Dobra:").grid(row=0, column=2)
    tk.Label(g.frame_dobra, text="Metade Dobra:").grid(row=0, column=3)

    for i in range(1, g.n):
        g.frame_dobra.rowconfigure(0, weight=0)
        g.frame_dobra.rowconfigure(i, weight=0)

        tk.Label(g.frame_dobra, text=f"Aba {i}:").grid(row=i, column=0)

        setattr(g, f'aba{i}_entry_{w}', tk.Entry(g.frame_dobra, width=10, justify="center"))
        entry = getattr(g, f'aba{i}_entry_{w}')
        entry.grid(row=i, column=1, sticky='we', padx=2)
        entry.bind("<KeyRelease>", lambda event: calcular_dobra(w))
        
        setattr(g, f'medidadobra{i}_label_{w}', tk.Label(g.frame_dobra, relief="sunken", width=10))
        label = getattr(g, f'medidadobra{i}_label_{w}')
        label.grid(row=i, column=2, sticky='we', padx=2)
        label.bind("<Button-1>", lambda event, i=i: copiar('medida_dobra', i, w))
        
        setattr(g, f'metadedobra{i}_label_{w}', tk.Label(g.frame_dobra, relief="sunken", width=10))
        label = getattr(g, f'metadedobra{i}_label_{w}')
        label.grid(row=i, column=3, sticky='we', padx=2)
        label.bind("<Button-1>", lambda event, i=i: copiar('metade_dobra', i, w))

    tk.Label(g.frame_dobra, text="Medida do Blank:").grid(row=i+1, column=0, columnspan=2, sticky='e', padx=2)

    setattr(g, f'medida_blank_label_{w}', tk.Label(g.frame_dobra, relief="sunken", width=10))
    medida_blank = getattr(g, f'medida_blank_label_{w}')
    medida_blank.grid(row=i+1, column=2, sticky='we', padx=2)
    medida_blank.bind("<Button-1>", lambda event: copiar('blank', i, w))
                      
    setattr(g, f'metade_blank_label_{w}', tk.Label(g.frame_dobra, relief="sunken", width=10))
    metade_blank = getattr(g,f'metade_blank_label_{w}')
    metade_blank.grid(row=i+1, column=3, sticky='we', padx=2)
    metade_blank.bind("<Button-1>", lambda event: copiar('metade_blank', i, w))


