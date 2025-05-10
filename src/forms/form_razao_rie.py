'''
Módulo para exibir o formulário de cálculo de razão raio interno / espessura.
'''
import tkinter as tk
from tkinter import ttk
from src.utils.janelas import (no_topo, posicionar_janela)
from src.utils.utilitarios import obter_caminho_icone
from src.utils.calculos import razao_ri_espessura
from src.config import globals as g

def main(root):
    '''
    Inicializa e exibe o formulário de cálculo de razão raio interno / espessura.
    Configura a interface gráfica para exibir os valores e fatores K correspondentes.
    '''
    if g.RIE_FORM:
        g.RIE_FORM.destroy()

    g.RIE_FORM = tk.Toplevel(root)
    g.RIE_FORM.title("Raio Interno / Espessura")
    g.RIE_FORM.geometry("240x280")
    g.RIE_FORM.resizable(False, False)

    # Define o ícone
    icone_path = obter_caminho_icone()
    g.RIE_FORM.iconbitmap(icone_path)

    no_topo(g.RIE_FORM)
    posicionar_janela(g.RIE_FORM,None)

    main_frame = tk.Frame(g.RIE_FORM)
    main_frame.pack(pady=5, padx=5, fill='both', expand=True)

    main_frame.grid_rowconfigure(0, weight=0)
    main_frame.grid_rowconfigure(1, weight=1)
    main_frame.grid_columnconfigure(0, weight=0)
    main_frame.grid_columnconfigure(1, weight=1)

    tk.Label(main_frame, text='Razão Raio Interno / Espessura: ').grid(row=0, column=0, sticky='w')
    g.RAZAO_RIE_LBL = tk.Label(main_frame, text="",relief="sunken", width=20)
    g.RAZAO_RIE_LBL.grid(row=0, column=1, sticky='e', padx=5, pady=5)

    def create_table(main_frame, data):
        # Frame para a tabela e barra de rolagem
        table_frame = tk.Frame(main_frame)
        table_frame.grid(row=1, column=0, columnspan=2, sticky='nsew', padx=5, pady=5)

        # Configuração da barra de rolagem vertical
        scrollbar = tk.Scrollbar(table_frame, orient='vertical')
        scrollbar.pack(side='right', fill='y')

        # Configuração da tabela
        tree = ttk.Treeview(table_frame,
                            columns=('Raio/Esp', 'Fator K'),
                            show='headings',
                            yscrollcommand=scrollbar.set
                            )
        tree.heading('Raio/Esp', text='Raio/Esp')
        tree.heading('Fator K', text='Fator K')
        tree.column('Raio/Esp', width=100, anchor='center')
        tree.column('Fator K', width=100, anchor='center')

        # Vincula a barra de rolagem à tabela
        scrollbar.config(command=tree.yview)

        # Inserção dos dados na tabela
        for raio, fator_k in data.items():
            tree.insert('', 'end', values=(raio, fator_k))

        tree.pack(fill='both', expand=True)

    avisolabel = tk.Message(
        main_frame,
        text='Atenção: Os valores apresentados na tabela são teóricos. '
             'Utilize-os apenas na ausência de dados mais precisos.',
        width=220,
        justify='left',
        fg='red',
        font=('Arial', 10, 'bold')
    )
    avisolabel.grid(row=2, column=0, columnspan=2, sticky='w', padx=5, pady=5)

    razao_ri_espessura()
    create_table(main_frame, g.RAIO_K)

if __name__ == "__main__":
    main(None)
