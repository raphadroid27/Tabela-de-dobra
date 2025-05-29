'''
Cria o cabeçalho da interface gráfica com os campos de entrada e os rótulos correspondentes.
'''
import tkinter as tk
from tkinter import ttk
from src.utils.classes import tooltip as tp
from src.utils.interface import (atualizar_widgets,
                                 atualizar_toneladas_m,
                                 copiar
                                 )
from src.utils.interface import todas_funcoes

LARGURA = 9  # Largura padrão para os widgets

class CabecalhoUI:
    '''
    Classe para criar o cabeçalho da interface gráfica com os campos de entrada e os rótulos correspondentes.
    Esta classe contém métodos para criar rótulos e widgets de entrada, além de configurar o cabeçalho da interface.
    '''
    def __init__(self, root):
        '''
        Cria o cabeçalho da interface gráfica com os campos de entrada e os rótulos correspondentes.
        '''
        self.frame = tk.Frame(root)

        for i in range(4):
            self.frame.columnconfigure(i, weight=1)

        for i in range(8):
            self.frame.rowconfigure(i, weight=0)

        # Material
        self.criar_label(self.frame, "Material:", (0, 0))
        self.material_widget = self.criar_widget(self.frame, 'combobox',
                                                 (1, 0),
                                                 justify="center")
        self.material_widget.bind("<<ComboboxSelected>>",
                                  func=lambda event: todas_funcoes(self))
        tp.ToolTip(self.material_widget, "Selecione o material")

        # Espessura
        self.criar_label(self.frame, "Espessura:", (0, 1))
        self.espessura_widget = self.criar_widget(self.frame,
                                             'combobox',
                                             (1, 1),
                                             justify="center")
        self.espessura_widget.bind("<<ComboboxSelected>>",
                              func=lambda event: todas_funcoes(self))
        tp.ToolTip(self.espessura_widget, "Selecione a espessura da peça.")

        # Canal
        self.criar_label(self.frame, "Canal:", (0, 2))
        self.canal_widget = self.criar_widget(self.frame,
                                         'combobox',
                                         (1, 2),
                                         justify="center")
        self.canal_widget.bind("<<ComboboxSelected>>",
                          func=lambda event: todas_funcoes(self))
        tp.ToolTip(self.canal_widget, "Selecione o canal de dobra.")

        # Comprimento
        self.criar_label(self.frame, "Compr:", (0, 3))
        self.comprimento_widget = self.criar_widget(self.frame,
                                               'entry',
                                               (1, 3),
                                               justify="center")
        self.comprimento_widget.bind("<KeyRelease>",
                                func=lambda event: atualizar_toneladas_m())
        tp.ToolTip(self.comprimento_widget, "Digite o comprimento da peça em milímetros.")

        # Raio interno
        self.criar_label(self.frame, "Raio Int.:", (2, 0))
        self.raio_interno_widget = self.criar_widget(self.frame,
                                                'entry',
                                                (3, 0),
                                                justify="center")
        self.raio_interno_widget.bind("<KeyRelease>", func=lambda event: todas_funcoes(self))
        tp.ToolTip(self.raio_interno_widget, "Digite o raio interno da peça em milímetros.")

        # Fator K
        self.criar_label(self.frame, "Fator K:", (2, 1))
        self.fator_k_widget = self.criar_widget(self.frame,
                                           'label',
                                           (3, 1))
        self.fator_k_widget.bind("<Button-1>",
                            func=lambda event: copiar('fator_k'))
        tp.ToolTip(self.fator_k_widget, "Clique para copiar o fator K.")

        # Dedução
        self.criar_label(self.frame, "Dedução:", (2, 2))
        self.deducao_widget = self.criar_widget(self.frame,
                                           'label',
                                           (3, 2))
        self.deducao_widget.bind("<Button-1>",
                            func=lambda event: copiar('dedução'))
        tp.ToolTip(self.deducao_widget, "Clique para copiar a dedução.")

        # Offset
        self.criar_label(self.frame, "Offset:", (2, 3))
        self.offset_widget = self.criar_widget(self.frame,
                                          'label',
                                          (3, 3))
        self.offset_widget.bind("<Button-1>",
                           func=lambda event: copiar('offset'))
        tp.ToolTip(self.offset_widget, "Clique para copiar o offset.")

        # Dedução específica
        self.criar_label(self.frame, "Ded. Espec.:", (4, 0))
        self.deducao_especifica_widget = self.criar_widget(self.frame,
                                                      'entry',
                                                      (5, 0), fg="blue",
                                                      justify="center")
        self.deducao_especifica_widget.bind("<KeyRelease>",
                                       func=lambda event: todas_funcoes(self))
        tp.ToolTip(self.deducao_especifica_widget, "Digite a dedução específica da peça em milímetros.")

        # Aba mínima
        self.criar_label(self.frame, "Aba Mín.:", (4, 1))
        self.aba_minima_widget = self.criar_widget(self.frame, 'label', (5, 1))
        self.aba_minima_widget.grid()

        # Z90°
        self.criar_label(self.frame, "Ext. Z90°:", (4, 2))
        self.z90_widget = self.criar_widget(self.frame, 'label', (5, 2))
        self.z90_widget.grid()

        # tom/m
        self.criar_label(self.frame, "Ton/m:", (4, 3))
        self.ton_m_widget = self.criar_widget(self.frame, 'label', (5, 3))
        self.ton_m_widget.grid()

        # Observações
        self.criar_label(self.frame, "Observações:", (6, 0)).grid(columnspan=4)
        self.observacoes_widget = self.criar_widget(self.frame, 'label', (7, 0))
        self.observacoes_widget.grid(columnspan=4)

        atualizar_widgets(self, 'material')

    def criar_label(self, frame, texto, linha_coluna, **kwargs):
        '''
        Cria um rótulo (Label) no frame especificado.

        Args:
            frame (tk.Frame): Frame onde o rótulo será criado.
            texto (str): Texto do rótulo.
            linha_coluna (tuple): Tupla contendo a linha e a coluna onde o rótulo será posicionado.
            **kwargs: Argumentos adicionais para o widget Label.
        '''
        linha, coluna = linha_coluna
        label = tk.Label(frame,
                         width=LARGURA,
                         text=texto,
                         anchor='w',
                         **kwargs)
        label.grid(row=linha, column=coluna, sticky='w')
        return label

    def criar_widget(self, frame, tipo, linha_coluna, **kwargs):
        '''
        Cria um widget (Entry, Label ou Combobox) no frame especificado
        e o armazena em uma variável global.

        Args:
            frame (tk.Frame): Frame onde o widget será criado.
            tipo (str): Tipo do widget ('entry', 'label' ou 'combobox').
            linha_coluna (tuple): Tupla contendo a linha e a coluna onde o widget será posicionado.
            largura (int): Largura do widget.
            **kwargs: Argumentos adicionais para o widget.
        '''
        linha, coluna = linha_coluna
        if tipo == 'entry':
            widget = tk.Entry(frame, width=LARGURA, **kwargs)
        elif tipo == 'label':
            widget = tk.Label(frame, width=LARGURA, relief="sunken", **kwargs)
        elif tipo == 'combobox':
            widget = ttk.Combobox(frame, width=LARGURA, **kwargs)
        else:
            raise ValueError("Tipo de widget inválido. Use 'entry', 'label' ou 'combobox'.")

        widget.grid(row=linha, column=coluna, padx=2, sticky='we')
        return widget
