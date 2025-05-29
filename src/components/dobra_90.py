'''
Este módulo contém funções para criar e gerenciar o frame de dobras
'''
import tkinter as tk
from src.utils.interface import (calcular_dobra,
                                 copiar,
                                 focus_next_entry,
                                 focus_previous_entry
                                 )
from src.utils.classes import tooltip as tp

LARGURA = 12

class DobraUI:
    """
    Classe para criar o frame de dobras na interface gráfica.
    Esta classe contém métodos para criar o frame de dobras, configurar os widgets
    e atualizar os valores das dobras com base no número de abas (n).
    """

    def __init__(self, cabecalho_ui, frame, w):
        '''
        Cria o frame para as dobras, com base no valor de n.
        O frame é criado apenas uma vez, e os widgets são atualizados
        '''
        self.frame = tk.Frame(frame)

        self.n = 6  # Número padrão de abas

        for i in range(4):
            self.frame.columnconfigure(i, weight=1)

        self.entradas_dobras(cabecalho_ui, self.n, w)

    def entradas_dobras(self, cabecalho_ui, valor, w):
        '''
        Cria os widgets para as dobras, com base no valor de n.
        '''
        # Atualizar o valor de n
        self.n = valor

        # Adicionar widgets novamente
        labels = ['Medida Ext.', 'Medida Dobra', 'Metade Dobra']
        for label in labels:
            tk.Label(self.frame, text=label).grid(row=0, column=labels.index(label)+1)

        for i in range(1, self.n):
            self.frame.rowconfigure(0, weight=0)
            self.frame.rowconfigure(i, weight=0)

            tk.Label(self.frame, text=f"Aba {i}:").grid(row=i, column=0)

            setattr(self, f'aba{i}_entry_{w}', tk.Entry(self.frame, width=LARGURA, justify="center"))
            entry = getattr(self, f'aba{i}_entry_{w}')
            entry.grid(row=i, column=1, sticky='we', padx=2)
            entry.bind("<KeyRelease>", lambda event: calcular_dobra(cabecalho_ui, self, w))
            tp.ToolTip(entry, "Insira o valor da dobra.")

            # Adicionar navegação com teclas direcionais
            entry.bind("<Down>", lambda event, i=i: focus_next_entry(i, w))
            entry.bind("<Up>", lambda event, i=i: focus_previous_entry(i, w))
            entry.bind("<Return>", lambda event, i=i: focus_next_entry(i, w))

            setattr(self, f'medidadobra{i}_label_{w}', tk.Label(self.frame,
                                                            relief="sunken",
                                                            width=LARGURA))
            label = getattr(self, f'medidadobra{i}_label_{w}')
            label.grid(row=i, column=2, sticky='we', padx=2)
            label.bind("<Button-1>", lambda event, i=i: copiar('medida_dobra', i, w))
            tp.ToolTip(label, "Clique para copiar a medida da dobra.")

            setattr(self, f'metadedobra{i}_label_{w}', tk.Label(self.frame,
                                                            relief="sunken",
                                                            width=LARGURA))
            label = getattr(self, f'metadedobra{i}_label_{w}')
            label.grid(row=i, column=3, sticky='we', padx=2)
            label.bind("<Button-1>", lambda event, i=i: copiar('metade_dobra', i, w))
            tp.ToolTip(label, "Clique para copiar a metade da dobra.")

        tk.Label(self.frame, text="Medida do Blank:").grid(row=i+1,
                                                            column=0,
                                                            columnspan=2,
                                                            sticky='e',
                                                            padx=2)

        setattr(self, f'medida_blank_label_{w}', tk.Label(self.frame,
                                                    relief="sunken",
                                                    width=LARGURA))
        medida_blank = getattr(self, f'medida_blank_label_{w}')
        medida_blank.grid(row=i+1, column=2, sticky='we', padx=2)
        medida_blank.bind("<Button-1>", lambda event: copiar('blank', i, w))
        tp.ToolTip(medida_blank, "Clique para copiar a medida do blank.")

        setattr(self, f'metade_blank_label_{w}', tk.Label(self.frame,
                                                    relief="sunken",
                                                    width=LARGURA))
        metade_blank = getattr(self, f'metade_blank_label_{w}')
        metade_blank.grid(row=i+1, column=3, sticky='we', padx=2)
        metade_blank.bind("<Button-1>", lambda event: copiar('metade_blank', i, w))
        tp.ToolTip(metade_blank, "Clique para copiar a metade do blank.")
