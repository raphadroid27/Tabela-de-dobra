"""
Este módulo contém funções para criar e gerenciar o frame de dobras
com widgets auto-ajustáveis para melhor responsividade.
"""

from dataclasses import dataclass
from typing import Tuple, Any
from PySide6.QtWidgets import QGroupBox, QLabel, QLineEdit, QGridLayout
from PySide6.QtCore import Qt
from src.config import globals as g
from src.utils.interface import (
    copiar, focus_next_entry, focus_previous_entry, calcular_valores)
from src.utils.estilo import aplicar_estilo_widget_auto_ajustavel

# Constantes para widgets auto-ajustáveis
WIDGET_HEIGHT = 20
WIDGET_MIN_WIDTH = 60


@dataclass
class ConfigLabelResultado:
    """Configuração para criação de labels de resultado."""
    layout: Any
    nome_global: str
    pos: Tuple[int, int]
    tooltip_text: str
    i: int
    w: str
    copy_type: str


@dataclass
class ConfigEntry:
    """Configuração para criação de entries de dobra."""
    layout: Any
    nome_global: str
    pos: Tuple[int, int]
    w: str
    i: int


def criar_label_header(layout, texto, pos):
    """
    Cria um label de cabeçalho com estilo uniforme.

    Args:
        layout: Layout onde o label será adicionado
        texto: Texto do label
        pos: Posição (linha, coluna) no layout

    Returns:
        QLabel criado
    """
    linha, coluna = pos
    header_label = QLabel(texto)
    header_label.setFixedHeight(WIDGET_HEIGHT)
    header_label.setMinimumWidth(WIDGET_MIN_WIDTH)
    header_label.setAlignment(Qt.AlignCenter)
    layout.addWidget(header_label, linha, coluna)
    return header_label


def criar_label_aba(layout, texto, pos):
    """
    Cria um label de aba com largura fixa menor.

    Args:
        layout: Layout onde o label será adicionado
        texto: Texto do label
        pos: Posição (linha, coluna) no layout

    Returns:
        QLabel criado
    """
    linha, coluna = pos
    aba_label = QLabel(texto)
    aba_label.setFixedHeight(WIDGET_HEIGHT)
    aba_label.setFixedWidth(50)  # Largura fixa menor para labels de aba
    aba_label.setAlignment(Qt.AlignCenter)
    layout.addWidget(aba_label, linha, coluna)
    return aba_label


def configurar_eventos_entry(entry, config: ConfigEntry):
    """
    Configura os eventos de um entry de dobra.

    Args:
        entry: Widget QLineEdit
        config: Configuração do entry
    """
    # Conectar eventos
    entry.textChanged.connect(calcular_valores)
    entry.returnPressed.connect(lambda: focus_next_entry(config.i, config.w))

    def custom_key_press_event(event):
        if event.key() == Qt.Key_Down:
            focus_next_entry(config.i, config.w)
        elif event.key() == Qt.Key_Up:
            focus_previous_entry(config.i, config.w)
        else:
            QLineEdit.keyPressEvent(entry, event)

    entry.keyPressEvent = custom_key_press_event
    entry.setToolTip("Insira o valor da dobra.")


def criar_entry_dobra(config: ConfigEntry):
    """
    Cria um LineEdit para entrada de dados de dobra com auto-ajuste.

    Args:
        config: Configuração encapsulada do entry

    Returns:
        QLineEdit criado
    """
    linha, coluna = config.pos
    entry = QLineEdit()
    entry.setAlignment(Qt.AlignCenter)
    entry.setFixedHeight(WIDGET_HEIGHT)
    entry.setMinimumWidth(WIDGET_MIN_WIDTH)

    # Aplicar estilo auto-ajustável
    aplicar_estilo_widget_auto_ajustavel(entry, 'lineedit')

    setattr(g, config.nome_global, entry)
    config.layout.addWidget(entry, linha, coluna)

    # Configurar eventos
    configurar_eventos_entry(entry, config)

    return entry


def criar_label_resultado(config: ConfigLabelResultado):
    """
    Cria um label de resultado com auto-ajuste e funcionalidade de cópia.

    Args:
        config: Configuração encapsulada do label

    Returns:
        QLabel criado
    """
    linha, coluna = config.pos
    label = QLabel()
    label.setFrameShape(QLabel.Shape.Panel)
    label.setFrameShadow(QLabel.Shadow.Sunken)
    label.setFixedHeight(WIDGET_HEIGHT)
    label.setMinimumWidth(WIDGET_MIN_WIDTH)
    label.setAlignment(Qt.AlignCenter)

    setattr(g, config.nome_global, label)
    config.layout.addWidget(label, linha, coluna)

    # Configurar eventos e tooltip
    label.mousePressEvent = lambda event: copiar(
        config.copy_type, config.i, config.w)
    label.setToolTip(config.tooltip_text)

    return label


def dobras(w):
    """
    Cria e retorna o frame de dobras com widgets auto-ajustáveis.

    Args:
        w: Sufixo identificador para widgets globais.

    Returns:
        QGroupBox configurado com os campos de dobras auto-ajustáveis.
    """
    g.FRAME_DOBRA = QGroupBox()
    g.FRAME_DOBRA.setFlat(True)
    g.FRAME_DOBRA.setStyleSheet('QGroupBox { margin-top: 0px; }')
    layout = QGridLayout(g.FRAME_DOBRA)
    layout.setContentsMargins(10, 0, 10, 0)
    layout.setSpacing(5)

    g.FRAME_DOBRA.setLayout(layout)

    _configurar_layout_dobra(layout)
    _criar_headers(layout)
    _criar_entradas_e_resultados(layout, w)
    _criar_labels_blank(layout, w)

    return g.FRAME_DOBRA


def _configurar_layout_dobra(layout):
    """Configura o layout com responsividade e espaçamento adequado."""

    # Configurar primeira coluna (labels de aba) com largura fixa
    layout.setColumnMinimumWidth(0, 50)
    layout.setColumnStretch(0, 0)

    # Configurar colunas de dados com expansão proporcional
    for col in range(1, 4):
        layout.setColumnStretch(col, 1)
        layout.setColumnMinimumWidth(col, WIDGET_MIN_WIDTH)

    # Configurar espaçamento
    layout.setHorizontalSpacing(5)
    layout.setVerticalSpacing(3)


def _criar_headers(layout):
    """Cria os cabeçalhos das colunas com widgets auto-ajustáveis."""
    headers = ['Medida Ext.:', 'Medida Dobra:', 'Metade Dobra:']

    for i, label_text in enumerate(headers):
        criar_label_header(layout, label_text, (0, i + 1))


def _criar_entradas_e_resultados(layout, w):
    """Cria as entradas e labels de resultado para cada aba."""
    for i in range(1, g.N):
        # Label da aba
        criar_label_aba(layout, f"Aba {i}:", (i, 0))

        # Entry para medida externa
        config_entry = ConfigEntry(
            layout=layout,
            nome_global=f'aba{i}_entry_{w}',
            pos=(i, 1),
            w=w,
            i=i
        )
        criar_entry_dobra(config_entry)

        # Label para medida da dobra
        config_medida = ConfigLabelResultado(
            layout=layout,
            nome_global=f'medidadobra{i}_label_{w}',
            pos=(i, 2),
            tooltip_text="Clique para copiar a medida da dobra.",
            i=i,
            w=w,
            copy_type='medida_dobra'
        )
        criar_label_resultado(config_medida)

        # Label para metade da dobra
        config_metade = ConfigLabelResultado(
            layout=layout,
            nome_global=f'metadedobra{i}_label_{w}',
            pos=(i, 3),
            tooltip_text="Clique para copiar a metade da dobra.",
            i=i,
            w=w,
            copy_type='metade_dobra'
        )
        criar_label_resultado(config_metade)


def _criar_labels_blank(layout, w):
    """Cria os labels do blank com widgets auto-ajustáveis."""
    # Label "Medida do Blank:"
    blank_label = QLabel("Medida do Blank:")
    blank_label.setAlignment(Qt.AlignCenter)
    blank_label.setFixedHeight(WIDGET_HEIGHT)
    layout.addWidget(blank_label, g.N, 0, 1, 2)

    # Label da medida do blank
    config_blank = ConfigLabelResultado(
        layout=layout,
        nome_global=f'medida_blank_label_{w}',
        pos=(g.N, 2),
        tooltip_text="Clique para copiar a medida do blank.",
        i=g.N,
        w=w,
        copy_type='blank'
    )
    criar_label_resultado(config_blank)

    # Label da metade do blank
    config_metade_blank = ConfigLabelResultado(
        layout=layout,
        nome_global=f'metade_blank_label_{w}',
        pos=(g.N, 3),
        tooltip_text="Clique para copiar a metade do blank.",
        i=g.N,
        w=w,
        copy_type='metade_blank'
    )
    criar_label_resultado(config_metade_blank)
