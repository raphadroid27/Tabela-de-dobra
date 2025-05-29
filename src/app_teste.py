'''
# Formulário Principal do Aplicativo de Cálculo de Dobra
'''

import os
import sys

# Adiciona o diretório raiz do projeto ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import tkinter as tk
from src.components.cabecalho import CabecalhoUI
from src.components.dobra_90 import DobraUI
from src.components import botoes

def carregar_interface(frame_superior, dobras_ui):
    '''
    Atualiza o cabeçalho e recria os widgets no frame de dobras.

    Args:
        frame_superior (tk.Frame): Frame onde os widgets serão adicionados.
    '''

    # Limpar widgets antigos no frame superior
    for widget in frame_superior.winfo_children():
        widget.destroy()

    # Adicionar o cabeçalho principal
    cabecalho_ui = CabecalhoUI(frame_superior, dobras_ui)
    cabecalho_ui.frame.grid(row=0, column=0, sticky='wens', ipadx=2, ipady=2)

    # Adicionar widgets de dobras
    dobras_ui = DobraUI(cabecalho_ui, frame_superior, w=1)  # Adicione o argumento 'w'
    dobras_ui.frame.grid(row=1, column=0, sticky='wens', ipadx=2, ipady=2)

    # Adicionar botões
    botoes.criar_botoes(self=None, root=frame_superior).grid(row=2, column=0, sticky='wens', ipadx=2, ipady=2)

def configurar_frames(app, dobras_ui):
    '''
    Configura os frames principais da janela.
    '''
    frame_superior = tk.LabelFrame(app)
    frame_superior.pack(fill='both', expand=True, padx=10, pady=10)

    frame_superior.columnconfigure(0, weight=1)
    frame_superior.rowconfigure(0, weight=1)
    frame_superior.rowconfigure(1, weight=1)

    carregar_interface(frame_superior, dobras_ui)

def main():
    '''
    Função principal que inicializa a interface gráfica do aplicativo.
    '''
    app = tk.Tk()
    app.title("Cálculo de Dobra")
    app.geometry('340x400')
    app.resizable(False, False)

    # Inicializar valores globais necessários
    if not hasattr(g, 'VALORES_W'):
        g.VALORES_W = [1]  # Definir apenas uma coluna para teste
    if not hasattr(g, 'N'):
        g.N = 6  # Número de abas padrão

    # Criar uma instância de DobraUI
    frame_superior = tk.LabelFrame(app)
    dobras_ui = DobraUI(None, frame_superior, w=1)  # Passe None para cabecalho_ui temporariamente

    # Passar dobras_ui como argumento
    configurar_frames(app, dobras_ui)

    app.mainloop()

if __name__ == "__main__":
    main()
