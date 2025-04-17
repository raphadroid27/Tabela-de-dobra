import tkinter as tk
from tkinter import ttk
import globals as g

def criar_aba3(notebook):
    aba3 = ttk.Frame(notebook)
    aba3.pack(fill='both', expand=True)

    notebook.add(aba3, text='Relação raio e fator K')
    
    # Crie um Frame para agrupar os Labels na mesma linha
    frame = tk.Frame(aba3)
    frame.pack(fill='both', expand=True, pady=5)
    
    tk.Label(frame, text='Raio interno / espessura: ').pack(side=tk.LEFT)
    g.RAZAO_RIE_LBL = tk.Label(frame, text="",relief="sunken",width=20)
    g.RAZAO_RIE_LBL.pack(side=tk.LEFT)
    
    def create_table(aba3, data):
        tree = ttk.Treeview(aba3, columns=('Raio/Esp', 'Fator K'), show='headings')
        tree.heading('Raio/Esp', text='Raio/Esp')
        tree.heading('Fator K', text='Fator K')
        tree.column('Raio/Esp', width=100)
        tree.column('Fator K', width=100)

        for raio, fator_k in data.items():
            tree.insert('', 'end', values=(raio, fator_k))

        tree.pack(fill='both', expand=True)

    create_table(aba3, g.RAIO_K)