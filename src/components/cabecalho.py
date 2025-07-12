"""
Cria o cabeçalho da interface gráfica com os campos de entrada e os rótulos correspondentes.
"""

from PySide6.QtWidgets import QGroupBox, QGridLayout, QLabel, QComboBox, QLineEdit
from PySide6.QtCore import Qt
from src.config import globals as g
from src.utils.interface import (
    atualizar_widgets, calcular_valores, copiar, canal_tooltip, aplicar_medida_borda_espaco)


def criar_label(layout, texto, linha_coluna):
    """
    Cria e adiciona um QLabel ao layout na posição especificada.

    Args:
        layout: Layout onde o label será adicionado.
        texto: Texto a ser exibido no label.
        linha_coluna: Tupla (linha, coluna) para posicionamento no layout.

    Returns:
        QLabel criado e adicionado ao layout.
    """
    linha, coluna = linha_coluna
    label = QLabel(texto)
    label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    layout.addWidget(label, linha, coluna)
    return label


def criar_widget(layout, tipo, nome_global, pos, **kwargs):
    """
    Cria e adiciona um widget ao layout, associando-o a um nome global.

    Args:
        layout: Layout onde o widget será adicionado.
        tipo: Tipo do widget ('label', 'combobox', 'entry').
        nome_global: Nome do atributo global para armazenar o widget.
        pos: Posição no layout.
        **kwargs: Argumentos adicionais para o widget.

    Returns:
        Widget criado e adicionado ao layout.
    """
    if tipo == 'label':
        widget = QLabel(kwargs.pop('text', ''))
        widget.setFrameShape(QLabel.Shape.Panel)
        widget.setFrameShadow(QLabel.Shadow.Sunken)
        widget.setFixedHeight(20)
        widget.setAlignment(Qt.AlignCenter)
    elif tipo == 'combobox':
        widget = QComboBox(**kwargs)
        widget.setFixedHeight(20)
    elif tipo == 'entry':
        widget = QLineEdit(**kwargs)
        widget.setFixedHeight(20)
        widget.setAlignment(Qt.AlignCenter)
    else:
        return None
    layout.addWidget(widget, *pos)
    setattr(g, nome_global, widget)
    return widget


def _criar_linha_1(layout):
    criar_label(layout, "Material", (0, 0))
    criar_label(layout, "Espessura", (0, 1))
    criar_label(layout, "Canal", (0, 2))
    criar_label(layout, "Comprimento", (0, 3))

    mat_comb = criar_widget(layout, 'combobox', 'MAT_COMB', (1, 0))
    esp_comb = criar_widget(layout, 'combobox', 'ESP_COMB', (1, 1))
    canal_comb = criar_widget(layout, 'combobox', 'CANAL_COMB', (1, 2))
    compr_entry = criar_widget(layout, 'entry', 'COMPR_ENTRY', (1, 3))

    mat_comb.setToolTip("Selecione o material.")
    esp_comb.setToolTip("Selecione a espessura.")
    canal_comb.setToolTip("Selecione o canal de dobra.")
    compr_entry.setToolTip("Digite o comprimento.")

    compr_entry.textChanged.connect(calcular_valores)
    return mat_comb, esp_comb, canal_comb, compr_entry


def _criar_linha_2(layout):
    criar_label(layout, "Raio Interno", (2, 0))
    criar_label(layout, "Fator K", (2, 1))
    criar_label(layout, "Dedução", (2, 2))
    criar_label(layout, "Offset", (2, 3))

    ri_entry = criar_widget(layout, 'entry', 'RI_ENTRY', (3, 0))
    k_lbl = criar_widget(layout, 'label', 'K_LBL', (3, 1))
    ded_lbl = criar_widget(layout, 'label', 'DED_LBL', (3, 2))
    offset_lbl = criar_widget(layout, 'label', 'OFFSET_LBL', (3, 3))

    ri_entry.setToolTip("Digite o raio interno em milímetros.")
    k_lbl.setToolTip("Fator K calculado com base no raio interno.")
    ded_lbl.setToolTip("Dedução de dobra.")
    offset_lbl.setToolTip("Offset calculado com base no raio interno.")

    ri_entry.textChanged.connect(calcular_valores)
    k_lbl.mousePressEvent = lambda event: copiar('fator_k')
    ded_lbl.mousePressEvent = lambda event: copiar('dedução')
    offset_lbl.mousePressEvent = lambda event: copiar('offset')
    return ri_entry, k_lbl, ded_lbl, offset_lbl


def _criar_linha_3(layout):
    criar_label(layout, "Ded. Espec.", (4, 0))
    criar_label(layout, "Aba Mín.", (4, 1))
    criar_label(layout, "Ext. Z90°", (4, 2))
    criar_label(layout, "Força", (4, 3))

    ded_espec_entry = criar_widget(layout, 'entry', 'DED_ESPEC_ENTRY', (5, 0))
    aba_ext_lbl = criar_widget(layout, 'label', 'ABA_EXT_LBL', (5, 1))
    z_ext_lbl = criar_widget(layout, 'label', 'Z_EXT_LBL', (5, 2))
    forca_lbl = criar_widget(layout, 'label', 'FORCA_LBL', (5, 3))

    ded_espec_entry.setToolTip("Digite a dedução específica em milímetros.")
    aba_ext_lbl.setToolTip("Medida da aba mínima.")
    z_ext_lbl.setToolTip("Medida de Z90° mínima.")
    forca_lbl.setToolTip("Força necessária para a dobra.")

    ded_espec_entry.textChanged.connect(calcular_valores)
    return ded_espec_entry, aba_ext_lbl, z_ext_lbl, forca_lbl


def _criar_observacoes(layout):
    obs_label = criar_label(layout, "Observações:", (6, 0))
    layout.addWidget(obs_label, 6, 0, 1, 4)
    obs_widget = criar_widget(layout, 'label', 'OBS_LBL', (7, 0))
    layout.addWidget(obs_widget, 7, 0, 1, 4)
    obs_widget.setToolTip("Observações sobre a dobra ou material.")


def _conectar_eventos(mat_comb, esp_comb, canal_comb, compr_entry):
    if mat_comb:
        mat_comb.currentTextChanged.connect(
            lambda: atualizar_widgets('espessura'))
    if esp_comb:
        esp_comb.currentTextChanged.connect(lambda: atualizar_widgets('canal'))
    if canal_comb:
        canal_comb.currentTextChanged.connect(
            lambda: atualizar_widgets('dedução'))
        canal_comb.currentTextChanged.connect(canal_tooltip)
    if compr_entry:
        compr_entry.textChanged.connect(calcular_valores)
    canal_tooltip()


def cabecalho():
    """
    Monta o cabeçalho da interface gráfica com todos os campos e rótulos.

    Returns:
        QGroupBox contendo o cabeçalho completo.
    """
    frame_cabecalho = QGroupBox()
    layout = QGridLayout(frame_cabecalho)
    aplicar_medida_borda_espaco(layout)
    for col in range(0, 4):
        layout.setColumnStretch(col, 1)
    mat_comb, esp_comb, canal_comb, compr_entry = _criar_linha_1(layout)
    _criar_linha_2(layout)
    _criar_linha_3(layout)
    _criar_observacoes(layout)
    _conectar_eventos(mat_comb, esp_comb, canal_comb, compr_entry)
    return frame_cabecalho
