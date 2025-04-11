'''
Este módulo contém funções para criar e gerenciar o frame de dobras
'''
import tkinter as tk
import globals as g
from funcoes import calcular_dobra, copiar, focus_next_entry, focus_previous_entry

LARGURA = 10

def dobras(frame, w):
    '''
    Cria o frame para as dobras, com base no valor de n.
    O frame é criado apenas uma vez, e os widgets são atualizados
    '''
    g.FRAME_DOBRA = tk.Frame(frame)

    for i in range(0, 4):
        g.FRAME_DOBRA.columnconfigure(i, weight=1)

    entradas_dobras(g.N, w)
    return g.FRAME_DOBRA

def entradas_dobras(valor, w):
    '''
    Cria os widgets para as dobras, com base no valor de n.'''
    # Atualizar o valor de n
    g.N = valor

    # Adicionar widgets novamente
    labels = ['Medida Ext.', 'Medida Dobra', 'Metade Dobra']
    for label in labels:
        tk.Label(g.FRAME_DOBRA, text=label).grid(row=0, column=labels.index(label)+1)

    for i in range(1, g.N):
        g.FRAME_DOBRA.rowconfigure(0, weight=0)
        g.FRAME_DOBRA.rowconfigure(i, weight=0)

        tk.Label(g.FRAME_DOBRA, text=f"Aba {i}:").grid(row=i, column=0)

        setattr(g, f'aba{i}_entry_{w}', tk.Entry(g.FRAME_DOBRA, width=LARGURA, justify="center"))
        entry = getattr(g, f'aba{i}_entry_{w}')
        entry.grid(row=i, column=1, sticky='we', padx=2)
        entry.bind("<KeyRelease>", lambda event: calcular_dobra(w))

        # Adicionar navegação com teclas direcionais
        entry.bind("<Down>", lambda event, i=i: focus_next_entry(i, w))
        entry.bind("<Up>", lambda event, i=i: focus_previous_entry(i, w))

        setattr(g, f'medidadobra{i}_label_{w}', tk.Label(g.FRAME_DOBRA, relief="sunken", width=LARGURA))
        label = getattr(g, f'medidadobra{i}_label_{w}')
        label.grid(row=i, column=2, sticky='we', padx=2)
        label.bind("<Button-1>", lambda event, i=i: copiar('medida_dobra', i, w))

        setattr(g, f'metadedobra{i}_label_{w}', tk.Label(g.FRAME_DOBRA, relief="sunken", width=LARGURA))
        label = getattr(g, f'metadedobra{i}_label_{w}')
        label.grid(row=i, column=3, sticky='we', padx=2)
        label.bind("<Button-1>", lambda event, i=i: copiar('metade_dobra', i, w))

    tk.Label(g.FRAME_DOBRA, text="Medida do Blank:").grid(row=i+1,
                                                          column=0,
                                                          columnspan=2,
                                                          sticky='e',
                                                          padx=2)

    setattr(g, f'medida_blank_label_{w}', tk.Label(g.FRAME_DOBRA,
                                                   relief="sunken",
                                                   width=LARGURA))
    medida_blank = getattr(g, f'medida_blank_label_{w}')
    medida_blank.grid(row=i+1, column=2, sticky='we', padx=2)
    medida_blank.bind("<Button-1>", lambda event: copiar('blank', i, w))

    setattr(g, f'metade_blank_label_{w}', tk.Label(g.FRAME_DOBRA,
                                                   relief="sunken",
                                                   width=LARGURA))
    metade_blank = getattr(g,f'metade_blank_label_{w}')
    metade_blank.grid(row=i+1, column=3, sticky='we', padx=2)
    metade_blank.bind("<Button-1>", lambda event: copiar('metade_blank', i, w))
