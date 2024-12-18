import tkinter as tk
from tkinter import ttk

def criar_aba2(notebook):
    aba2 = ttk.Frame(notebook, width=400, height=400)
    aba2.pack(fill='both', expand=True)
    notebook.add(aba2, text='Aba 2')

    # Conteúdo da Aba 2
    label2 = tk.Label(aba2, text="Outra aba")
    label2.pack(pady=10)

    return aba2