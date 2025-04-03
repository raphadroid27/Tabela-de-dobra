"""
Módulo responsável por criar o frame de avisos na interface gráfica.
"""

import tkinter as tk
from tkinter import ttk

def avisos(root):
    """
    Cria um frame contendo avisos para o usuário.

    Args:
        root: O widget pai onde o frame será inserido.

    Returns:
        ttk.Frame: O frame contendo os avisos.
    """
    avisos_textos = [
        "1. Verifique se o material e a espessura estão corretos.",
        "2. Verifique se o canal está correto."
    ]

    frame_avisos = ttk.Frame(root)
    frame_avisos.grid(row=0, column=0, sticky='nsew', padx=10)

    for aviso in avisos_textos:
        aviso_label = tk.Label(frame_avisos, text=aviso)
        aviso_label.pack(anchor='w', padx=5, pady=2)

    return frame_avisos
