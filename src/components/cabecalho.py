"""
Cria o cabeçalho da interface gráfica com os campos de entrada e os rótulos correspondentes.
"""
from PySide6.QtWidgets import QGroupBox, QGridLayout, QLabel, QComboBox, QLineEdit
from PySide6.QtCore import Qt
from src.config import globals as g
from src.utils.interface import (
    atualizar_widgets,
    calcular_valores,
    copiar
)


def criar_label(layout, texto, linha_coluna, **kwargs):
    """
    Cria um rótulo (QLabel) no layout especificado.

    Args:
        layout (QGridLayout): Layout onde o rótulo será criado.
        texto (str): Texto do rótulo.
        linha_coluna (tuple): Tupla contendo a linha e a coluna onde o rótulo será posicionado.
        **kwargs: Argumentos adicionais para o widget QLabel.
    """
    linha, coluna = linha_coluna
    label = QLabel(texto)
    label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    layout.addWidget(label, linha, coluna)
    return label


def criar_widget(layout, tipo, nome_global, pos, **kwargs):
    """
    Cria e configura um widget, o adiciona ao layout e o armazena em g.
    """
    justify = kwargs.pop('justify', None)

    if tipo == 'label':
        widget = QLabel(kwargs.pop('text', ''))
        widget.setFrameShape(QLabel.Shape.Panel)
        widget.setFrameShadow(QLabel.Shadow.Sunken)
        widget.setFixedHeight(20)  # Altura fixa
        widget.setAlignment(Qt.AlignCenter)
    
    elif tipo == 'combobox':
        widget = QComboBox(**kwargs)
        widget.setFixedHeight(20)  # Altura fixa
        # QComboBox não tem uma propriedade 'justify' simples.
        # A centralização pode ser feita se for editável ou com um delegate.
        # Por enquanto, vamos usar o alinhamento padrão.
    
    elif tipo == 'entry':
        widget = QLineEdit(**kwargs)
        widget.setFixedHeight(20)  # Altura fixa
        if justify == 'center':
            widget.setAlignment(Qt.AlignCenter)
        elif justify == 'right':
            widget.setAlignment(Qt.AlignRight)
        else:
            widget.setAlignment(Qt.AlignLeft)
    else:
        return None

    layout.addWidget(widget, *pos)
    setattr(g, nome_global, widget)
    return widget


def cabecalho(parent):
    """
    Cria o cabeçalho da interface gráfica com os campos de entrada e os rótulos correspondentes.
    """
    frame_cabecalho = QGroupBox()
    layout = QGridLayout(frame_cabecalho)
    
    # Configurar espaçamento e margens
    layout.setSpacing(5)  # Espaçamento entre widgets
    layout.setContentsMargins(5, 5, 5, 5)  # Margens internas
    
    # Configurar larguras das colunas para alinhamento com dobras
    # Colunas 0, 1, 2, 3: Larguras iguais e expansíveis (Material, Espessura, Canal, Comprimento)
    for col in range(0, 4):
        layout.setColumnStretch(col, 1)  # Expande igualmente


    # Labels da Linha 1
    criar_label(layout, "Material", (0, 0))
    criar_label(layout, "Espessura", (0, 1))
    criar_label(layout, "Canal", (0, 2))
    criar_label(layout, "Comprimento", (0, 3))


    # Widgets da Linha 1
    mat_comb = criar_widget(layout, 'combobox', 'MAT_COMB', (1, 0))
    esp_comb = criar_widget(layout, 'combobox', 'ESP_COMB', (1, 1))
    canal_comb = criar_widget(layout, 'combobox', 'CANAL_COMB', (1, 2))
    compr_entry = criar_widget(layout, 'entry', 'COMPR_ENTRY', (1, 3), justify="center")
    compr_entry.setToolTip("Digite o comprimento da peça em milímetros.")


    # Labels da Linha 2
    criar_label(layout, "Raio Interno", (2, 0))
    criar_label(layout, "Fator K", (2, 1))
    criar_label(layout, "Dedução", (2, 2))
    criar_label(layout, "Offset", (2, 3))


    # Widgets da Linha 2
    ri_entry = criar_widget(layout, 'entry', 'RI_ENTRY', (3, 0), justify="center")
    ri_entry.textChanged.connect(calcular_valores)
    ri_entry.setToolTip("Digite o raio interno da dobra em milímetros.")
    k_lbl = criar_widget(layout, 'label', 'K_LBL', (3, 1))
    k_lbl.mousePressEvent = lambda event: copiar('fator_k')
    ded_lbl = criar_widget(layout, 'label', 'DED_LBL', (3, 2))
    ded_lbl.mousePressEvent = lambda event: copiar('dedução')
    offset_lbl = criar_widget(layout, 'label', 'OFFSET_LBL', (3, 3))
    offset_lbl.mousePressEvent = lambda event: copiar('offset')


    # Labels da Linha 3
    criar_label(layout, "Ded. Espec.", (4, 0))
    criar_label(layout, "Aba Mín.", (4, 1))
    criar_label(layout, "Ext. Z90°", (4, 2))
    criar_label(layout, "Força", (4, 3))


    # Widgets da Linha 3
    ded_espec_entry = criar_widget(layout, 'entry', 'DED_ESPEC_ENTRY', (5, 0), justify="center")
    ded_espec_entry.textChanged.connect(calcular_valores)
    ded_espec_entry.setToolTip("Digite a dedução específica da peça em milímetros.")
    criar_widget(layout, 'label', 'ABA_EXT_LBL', (5, 1))
    criar_widget(layout, 'label', 'Z_EXT_LBL', (5, 2))
    criar_widget(layout, 'label', 'FORCA_LBL', (5, 3))


    # Observações
    obs_label = criar_label(layout, "Observações:", (6, 0))
    layout.addWidget(obs_label, 6, 0, 1, 4)  # columnspan 4
    obs_widget = criar_widget(layout, 'label', 'OBS_LBL', (7, 0))
    layout.addWidget(obs_widget, 7, 0, 1, 4)  # columnspan 4

    # Conectar eventos de mudança nas comboboxes após todos os widgets estarem criados
    if mat_comb:
        mat_comb.currentTextChanged.connect(lambda: atualizar_widgets('espessura'))
    if esp_comb:
        esp_comb.currentTextChanged.connect(lambda: atualizar_widgets('canal'))
    if canal_comb:
        canal_comb.currentTextChanged.connect(lambda: atualizar_widgets('dedução'))
    if compr_entry:
        compr_entry.textChanged.connect(calcular_valores)

    return frame_cabecalho
