'''
Módulo para exibir o formulário de cálculo de razão raio interno / espessura.
'''
import tkinter as tk
from tkinter import ttk
from src.utils.janelas import (no_topo, posicionar_janela)
from src.utils.utilitarios import obter_caminho_icone
from src.config import globals as g

def main(root):
    '''
    Inicializa e exibe o formulário de cálculo de razão raio interno / espessura.
    Configura a interface gráfica para exibir os valores e fatores K correspondentes.
    '''
    form = tk.Toplevel(root)
    form.geometry("340x420")
    form.resizable(False, False)

    # Define o ícone
    icone_path = obter_caminho_icone()
    form.iconbitmap(icone_path)

    no_topo(form)
    posicionar_janela(form,None)

    main_frame = tk.Frame(form)
    main_frame.pack(pady=5, padx=5, fill='both', expand=True)

    tk.Label(main_frame, text='Raio interno / espessura: ').pack(side=tk.LEFT)
    g.RAZAO_RIE_LBL = tk.Label(main_frame, text="",relief="sunken",width=20)
    g.RAZAO_RIE_LBL.pack(side=tk.LEFT)

    def create_table(main_frame, data):
        tree = ttk.Treeview(main_frame, columns=('Raio/Esp', 'Fator K'), show='headings')
        tree.heading('Raio/Esp', text='Raio/Esp')
        tree.heading('Fator K', text='Fator K')
        tree.column('Raio/Esp', width=100)
        tree.column('Fator K', width=100)

        for raio, fator_k in data.items():
            tree.insert('', 'end', values=(raio, fator_k))

        tree.pack(fill='both', expand=True)

    create_table(main_frame, g.RAIO_K)

if __name__ == "__main__":
    main(None)
