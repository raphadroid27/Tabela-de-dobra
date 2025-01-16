import tkinter as tk
from tkinter import ttk

def criar_aba3(notebook):
    aba3 = ttk.Frame(notebook, width=400, height=400)
    aba3.pack(fill='both', expand=True)
    notebook.add(aba3, text='relação raio e fator K')

    raio_fator_k = {
    0.1: 0.23,
    0.2: 0.29,
    0.3: 0.32,
    0.4: 0.35,
    0.5: 0.37,
    0.6: 0.38,
    0.7: 0.39,
    0.8: 0.40,
    0.9: 0.41,
    1.0: 0.41,
    1.5: 0.44,
    2.0: 0.45,
    3.0: 0.46,
    4.0: 0.47,
    5.0: 0.48,
    6.0: 0.48,
    7.0: 0.49,
    8.0: 0.49,
    9.0: 0.50,
    10.0: 0.50
    }

    def create_table(aba3, data):
        tree = ttk.Treeview(aba3, columns=('Raio', 'Fator K'), show='headings')
        tree.heading('Raio', text='Raio')
        tree.heading('Fator K', text='Fator K')

        for raio, fator_k in data.items():
            tree.insert('', 'end', values=(raio, fator_k))

        tree.pack(fill='both', expand=True)

    create_table(aba3, raio_fator_k)