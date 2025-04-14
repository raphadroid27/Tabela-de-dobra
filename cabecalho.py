"""
Este módulo é responsável por criar o cabeçalho da interface gráfica, incluindo
os campos de entrada, rótulos e comboboxes necessários para a interação do usuário.
"""
import tkinter as tk
from tkinter import ttk
import tooltip as tp
import globals as g
from funcoes import atualizar_combobox, todas_funcoes, copiar, atualizar_toneladas_m

LARGURA = 9 # Largura padrão para os widgets

def criar_label(frame, texto, linha_coluna, **kwargs):
    """
    Cria um rótulo (Label) no frame especificado.

    Args:
        frame (tk.Frame): Frame onde o rótulo será criado.
        texto (str): Texto do rótulo.
        linha_coluna (tuple): Tupla contendo a linha e a coluna onde o rótulo será posicionado.
        **kwargs: Argumentos adicionais para o widget Label.
    """
    linha, coluna = linha_coluna
    label = tk.Label(frame, width=LARGURA,
             text=texto,
             anchor='w',
             **kwargs)
    label.grid(row=linha, column=coluna, sticky='w')
    return label

def criar_widget(frame, tipo, var_global, linha_coluna, **kwargs):
    """
    Cria um widget (Entry, Label ou Combobox) no frame especificado
    e o armazena em uma variável global.

    Args:
        frame (tk.Frame): Frame onde o widget será criado.
        tipo (str): Tipo do widget ('entry', 'label' ou 'combobox').
        var_global (str): Nome da variável global para armazenar o widget.
        linha_coluna (tuple): Tupla contendo a linha e a coluna onde o widget será posicionado.
        largura (int): Largura do widget.
        **kwargs: Argumentos adicionais para o widget.
    """
    linha, coluna = linha_coluna
    if tipo == 'entry':
        setattr(g, var_global, tk.Entry(frame, width=LARGURA, **kwargs))
    elif tipo == 'label':
        setattr(g, var_global, tk.Label(frame, width=LARGURA, relief="sunken", **kwargs))
    elif tipo == 'combobox':
        setattr(g, var_global, ttk.Combobox(frame, width=LARGURA, **kwargs))
    widget = getattr(g, var_global)
    widget.grid(row=linha, column=coluna, padx=2, sticky='we')
    return widget

def cabecalho(root):
    """
    Cria o cabeçalho da interface gráfica com os campos de entrada e os rótulos correspondentes.
    """
    frame_cabecalho = tk.Frame(root)

    for i in range(4):
        frame_cabecalho.columnconfigure(i, weight=1)

    for i in range(8):
        frame_cabecalho.rowconfigure(i, weight=0)

    # Material
    criar_label(frame_cabecalho, "Material:", (0, 0))
    criar_widget(frame_cabecalho, 'combobox', 'MAT_COMB', (1, 0), justify="center")
    g.MAT_COMB.bind("<<ComboboxSelected>>", func=lambda event: todas_funcoes())
    tp.ToolTip(g.MAT_COMB, "Selecione o material")

    # Espessura
    criar_label(frame_cabecalho, "Espessura:", (0, 1))
    criar_widget(frame_cabecalho, 'combobox', 'ESP_COMB', (1, 1), justify="center")
    g.ESP_COMB.bind("<<ComboboxSelected>>", func=lambda event: todas_funcoes())
    tp.ToolTip(g.ESP_COMB, "Selecione a espessura da peça.")

    # Canal
    criar_label(frame_cabecalho, "Canal:", (0, 2))
    criar_widget(frame_cabecalho, 'combobox', 'CANAL_COMB', (1, 2), justify="center")
    g.CANAL_COMB.bind("<<ComboboxSelected>>", func=lambda event: todas_funcoes())
    tp.ToolTip(g.CANAL_COMB, "Selecione o canal de dobra.")

    # Comprimento
    criar_label(frame_cabecalho, "Compr:", (0, 3))
    criar_widget(frame_cabecalho, 'entry', 'COMPR_ENTRY', (1, 3), justify="center")
    g.COMPR_ENTRY.bind("<KeyRelease>", func=lambda event: atualizar_toneladas_m())
    tp.ToolTip(g.COMPR_ENTRY, "Digite o comprimento da peça em milímetros.")

    # Raio interno
    criar_label(frame_cabecalho, "Raio Int.:", (2, 0))
    criar_widget(frame_cabecalho, 'entry', 'RI_ENTRY', (3, 0), justify="center")
    g.RI_ENTRY.bind("<KeyRelease>", func=lambda event: todas_funcoes())
    tp.ToolTip(g.RI_ENTRY, "Digite o raio interno da peça em milímetros.")

    # Fator K
    criar_label(frame_cabecalho, "Fator K:", (2, 1))
    criar_widget(frame_cabecalho, 'label', 'K_LBL', (3, 1))
    g.K_LBL.bind("<Button-1>", func=lambda event: copiar('fator_k'))
    tp.ToolTip(g.K_LBL, "Clique para copiar o fator K.")

    # Dedução
    criar_label(frame_cabecalho, "Dedução:", (2, 2))
    criar_widget(frame_cabecalho, 'label', 'DED_LBL', (3, 2))
    g.DED_LBL.bind("<Button-1>", func=lambda event: copiar('dedução'))
    tp.ToolTip(g.DED_LBL, "Clique para copiar a dedução.")

    # Offset
    criar_label(frame_cabecalho, "Offset:", (2, 3))
    criar_widget(frame_cabecalho, 'label', 'OFFSET_LBL', (3, 3))
    g.OFFSET_LBL.bind("<Button-1>", func=lambda event: copiar('offset'))
    tp.ToolTip(g.OFFSET_LBL, "Clique para copiar o offset.")

    # Dedução específica
    criar_label(frame_cabecalho, "Ded. Espec.:", (4, 0))
    criar_widget(frame_cabecalho, 'entry', 'DED_ESPEC_ENTRY', (5, 0), fg="blue", justify="center")
    g.DED_ESPEC_ENTRY.bind("<KeyRelease>", func=lambda event: todas_funcoes())
    tp.ToolTip(g.DED_ESPEC_ENTRY, "Digite a dedução específica da peça em milímetros.")

    # Aba mínima
    criar_label(frame_cabecalho, "Aba Mín.:", (4, 1))
    criar_widget(frame_cabecalho, 'label', 'ABA_EXT_LBL', (5, 1))
    tp.ToolTip(g.ABA_EXT_LBL, "Aba mínima externa.")

    # Z90°
    criar_label(frame_cabecalho, "Ext. Z90°:", (4, 2))
    criar_widget(frame_cabecalho, 'label', 'Z_EXT_LBL', (5, 2))
    tp.ToolTip(g.Z_EXT_LBL, "Medida externa mínima para Z90°.")

    # tom/m
    criar_label(frame_cabecalho, "Ton/m:", (4, 3))
    criar_widget(frame_cabecalho, 'label', 'FORCA_LBL', (5, 3))
    tp.ToolTip(g.FORCA_LBL, "Toneladas por metro.")

    # Observações
    criar_label(frame_cabecalho, "Observações:", (6, 0)).grid(columnspan=4)
    criar_widget(frame_cabecalho, 'label', 'OBS_LBL', (7, 0), anchor='w').grid(columnspan=4)

    atualizar_combobox('material')

    return frame_cabecalho
