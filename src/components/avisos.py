'''
Módulo responsável por criar o frame de avisos na interface gráfica.
'''
import tkinter as tk

def avisos(root):
    '''
    Cria um frame contendo avisos para o usuário.

    Args:
        root: O widget pai onde o frame será inserido.

    Returns:
        ttk.Frame: O frame contendo os avisos.
    '''
    avisos_textos = [
        "1. Xadrez → Laser sempre corta com a face xadrez para Baixo ↓.",
        "2. Corrugado → Laser sempre corta com a face do corrugado para Cima ↑.",
        "3. Ferramenta 'bigode': fazer alívio de dobra em abas maiores que 20mm."
    ]

    frame_avisos = tk.Frame(root)

    for aviso in avisos_textos:
        aviso_label = tk.Label(frame_avisos,
                               text=aviso,
                               anchor='w',
                               font=('Arial', 10),
                               wraplength=300,
                               justify='left'
                               )
        aviso_label.pack(anchor='w', padx=5, pady=2)

    return frame_avisos
