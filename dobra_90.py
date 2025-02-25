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

        # Armazenar os valores atuais
        valores = {}
        for i in range(1, g.n):
            entry = getattr(g, f'aba{i}_entry', None)
            if entry and entry.winfo_exists():
                valores[f'aba{i}_entry'] = entry.get()
            label = getattr(g, f'medidadobra{i}_label', None)
            if label and label.winfo_exists():
                valores[f'medidadobra{i}_label'] = label.cget("text")
            label = getattr(g, f'metadedobra{i}_label', None)
            if label and label.winfo_exists():
                valores[f'metadedobra{i}_label'] = label.cget("text")

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
            entry = getattr(g, f'aba{i}_entry')
            entry.grid(row=i, column=1, sticky='we', padx=2)
            entry.bind("<KeyRelease>", lambda event: calcular_dobra())
            # Restaurar valor
            if f'aba{i}_entry' in valores:
                entry.insert(0, valores[f'aba{i}_entry'])

            setattr(g, f'medidadobra{i}_label', tk.Label(frame_dobra, relief="sunken", width=10))
            label = getattr(g, f'medidadobra{i}_label')
            label.grid(row=i, column=2, sticky='we', padx=2)
            label.bind("<Button-1>", lambda event, i=i: copiar('medida_dobra', i))
            # Restaurar valor
            if f'medidadobra{i}_label' in valores:
                label.config(text=valores[f'medidadobra{i}_label'])

            setattr(g, f'metadedobra{i}_label', tk.Label(frame_dobra, relief="sunken", width=10))
            label = getattr(g, f'metadedobra{i}_label')
            label.grid(row=i, column=3, sticky='we', padx=2)
            label.bind("<Button-1>", lambda event, i=i: copiar('metade_dobra', i))
            # Restaurar valor
            if f'metadedobra{i}_label' in valores:
                label.config(text=valores[f'metadedobra{i}_label'])

        tk.Label(frame_dobra, text="Medida do Blank:").grid(row=i+1, column=0, columnspan=2, sticky='e', padx=2)

        g.medida_blank_label = tk.Label(frame_dobra, relief="sunken", width=10)
        g.medida_blank_label.grid(row=i+1, column=2, sticky='we', padx=2)
        g.medida_blank_label.bind("<Button-1>", lambda event: copiar('blank'))

        g.metade_blank_label = tk.Label(frame_dobra, relief="sunken", width=10)
        g.metade_blank_label.grid(row=i+1, column=3, sticky='we', padx=2)
        g.metade_blank_label.bind("<Button-1>", lambda event: copiar('metade_blank'))

        # Atualizar a geometria da janela principal
        if g.n == 6:
            g.principal_form.update_idletasks()
            g.principal_form.geometry(f"340x400")
        else:
            g.principal_form.update_idletasks()
            g.principal_form.geometry(f"340x500")

    frame_inferior = tk.Frame(root)
    frame_inferior.pack(fill='both', expand=True)

    frame_inferior.columnconfigure(0, weight=1)
    
    estado = tk.StringVar(value="+")

    def alternar_dobras():
        if estado.get() == "+":
            dobras(11)
            estado.set("-")
        else:
            dobras(6)
            estado.set("+")

        calcular_dobra()

    botao_alternar = tk.Button(frame_inferior, textvariable=estado, width=1, height=1, command=alternar_dobras)
    botao_alternar.grid(row=0, column=0, sticky='we', padx=12)

    dobras(g.n)
