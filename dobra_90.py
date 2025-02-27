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

    # Armazenar os valores atuais
    valores = {}
    for i in range(1, g.n):
        entry = getattr(g, f'aba{i}_entry_{w}', None)
        if entry and entry.winfo_exists():
            valores[f'aba{i}_entry_{w}'] = entry.get()
        label = getattr(g, f'medidadobra{i}_label_{w}', None)
        if label and label.winfo_exists():
            valores[f'medidadobra{i}_label_{w}'] = label.cget("text")
        label = getattr(g, f'metadedobra{i}_label_{w}', None)
        if label and label.winfo_exists():
            valores[f'metadedobra{i}_label_{w}'] = label.cget("text")

    # Remover widgets existentes
    for widget in g.frame_dobra.winfo_children():
        widget.destroy()

    # Adicionar widgets novamente
    tk.Label(g.frame_dobra, text="Medida Ext.:").grid(row=0, column=1)
    tk.Label(g.frame_dobra, text="Medida Dobra:").grid(row=0, column=2)
    tk.Label(g.frame_dobra, text="Metade Dobra:").grid(row=0, column=3)

    for i in range(1, g.n):
        g.frame_dobra.rowconfigure(0, weight=0)
        g.frame_dobra.rowconfigure(i, weight=0)

        tk.Label(g.frame_dobra, text=f"Aba {i}:").grid(row=i, column=0)

        setattr(g, f'aba{i}_entry_{w}', tk.Entry(g.frame_dobra, width=10))
        entry = getattr(g, f'aba{i}_entry_{w}')
        entry.grid(row=i, column=1, sticky='we', padx=2)
        entry.bind("<KeyRelease>", lambda event: calcular_dobra())
        # Restaurar valor
        if f'aba{i}_entry_{w}' in valores:
            entry.insert(0, valores[f'aba{i}_entry_{w}'])

        setattr(g, f'medidadobra{i}_label_{w}', tk.Label(g.frame_dobra, relief="sunken", width=10))
        label = getattr(g, f'medidadobra{i}_label_{w}')
        label.grid(row=i, column=2, sticky='we', padx=2)
        label.bind("<Button-1>", lambda event, i=i: copiar('medida_dobra', i))
        # Restaurar valor
        if f'medidadobra{i}_label_{w}' in valores:
            label.config(text=valores[f'medidadobra{i}_label_{w}'])

        setattr(g, f'metadedobra{i}_label_{w}', tk.Label(g.frame_dobra, relief="sunken", width=10))
        label = getattr(g, f'metadedobra{i}_label_{w}')
        label.grid(row=i, column=3, sticky='we', padx=2)
        label.bind("<Button-1>", lambda event, i=i: copiar('metade_dobra', i))
        # Restaurar valor
        if f'metadedobra{i}_label_{w}' in valores:
            label.config(text=valores[f'metadedobra{i}_label_{w}'])

    tk.Label(g.frame_dobra, text="Medida do Blank:").grid(row=i+1, column=0, columnspan=2, sticky='e', padx=2)

    # python
    setattr(g, f'medida_blank_label_{w}', tk.Label(g.frame_dobra, relief="sunken", width=10))
    medida_blank = getattr(g, f'medida_blank_label_{w}')
    medida_blank.grid(row=i+1, column=2, sticky='we', padx=2)
    medida_blank.bind("<Button-1>", lambda event: copiar('blank'))
                      
    setattr(g, f'metade_blank_label_{w}', tk.Label(g.frame_dobra, relief="sunken", width=10))
    metade_blank = getattr(g,f'metade_blank_label_{w}')
    metade_blank.grid(row=i+1, column=3, sticky='we', padx=2)
    metade_blank.bind("<Button-1>", lambda event: copiar('metade_blank'))

    # # Atualizar a geometria da janela principal
    # if g.n == 6:
    #     g.principal_form.update_idletasks()
    #     g.principal_form.geometry(f"340x400")
    # else:
    #     g.principal_form.update_idletasks()
    #     g.principal_form.geometry(f"340x500")


