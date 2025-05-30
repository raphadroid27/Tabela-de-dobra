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
from src.components.botoes import BotoesUI

class AppUI:
    '''
    Classe principal da interface gráfica do aplicativo.
    '''
    def __init__(self):
        '''
        Função principal que inicializa a interface gráfica do aplicativo.
        '''
        self.janela_principal = tk.Tk()
        self.janela_principal.title("Cálculo de Dobra")
        self.janela_principal.geometry('340x400')
        self.janela_principal.resizable(False, False)

        # Configurar a interface
        self.configurar_frames()

        # Iniciar o loop principal
        self.janela_principal.mainloop()

    def configurar_frames(self):
        '''
        Configura os frames principais da janela.
        '''
        self.frame = tk.LabelFrame(self.janela_principal)
        self.frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=1)
        self.frame.rowconfigure(2, weight=1)

        # Carregar os componentes da interface
        self.carregar_interface()

    def carregar_interface(self):
        '''
        Atualiza o cabeçalho e recria os widgets no frame de dobras.
        '''
        # Limpar widgets antigos no frame superior
        for widget in self.frame.winfo_children():
            widget.destroy()

        # Criar instância de DobraUI temporária para passar ao cabeçalho
        dobras_ui_temp = None

        # Adicionar o cabeçalho principal
        cabecalho_ui = CabecalhoUI(self.frame, dobras_ui_temp)
        cabecalho_ui.frame.grid(row=0, column=0, sticky='ewns', ipadx=2, ipady=2)

        # Adicionar widgets de dobras
        dobras_ui = DobraUI(cabecalho_ui, self.frame, w=1)
        dobras_ui.frame.grid(row=1, column=0, sticky='ewns', ipadx=2, ipady=2)

        # Atualizar a referência no cabeçalho
        cabecalho_ui.dobras_ui = dobras_ui

        # Adicionar botões
        botoes_ui = BotoesUI(self.frame, self)
        botoes_ui.frame.grid(row=2, column=0, sticky='ewns', ipadx=2, ipady=2)

if __name__ == "__main__":
    app = AppUI()