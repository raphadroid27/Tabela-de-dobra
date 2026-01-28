"""Cria e gerencia o frame de dobras com widgets auto-ajustáveis."""

from dataclasses import dataclass
from typing import Any, Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QGroupBox, QLabel, QLineEdit

from src.config import globals as g
from src.utils.utilitarios import resolver_expressao_no_line_edit
from src.utils.interface import (
    calcular_valores,
    copiar,
    focus_next_entry,
    focus_previous_entry,
)


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
    header_label.setObjectName("label_titulo")
    header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
    aba_label.setObjectName("label_titulo")
    aba_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
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

    # Apenas recalcula enquanto digita, sem resolver a expressão antes do usuário terminar
    entry.textChanged.connect(calcular_valores)

    def on_return_pressed():
        resolver_expressao_no_line_edit(entry)
        calcular_valores()  # Cálculo imediato ao pressionar Enter
        focus_next_entry(config.i, config.w)

    entry.returnPressed.connect(on_return_pressed)

    def on_focus_out_event(event):
        resolver_expressao_no_line_edit(entry)
        return QLineEdit.focusOutEvent(entry, event)

    def custom_key_press_event(event):
        if event.key() == Qt.Key.Key_Down:
            focus_next_entry(config.i, config.w)
        elif event.key() == Qt.Key.Key_Up:
            focus_previous_entry(config.i, config.w)
        else:
            QLineEdit.keyPressEvent(entry, event)

    entry.keyPressEvent = custom_key_press_event
    entry.focusOutEvent = on_focus_out_event


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
    entry.setAlignment(Qt.AlignmentFlag.AlignCenter)

    setattr(g, config.nome_global, entry)
    config.layout.addWidget(entry, linha, coluna)

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
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    setattr(g, config.nome_global, label)
    config.layout.addWidget(label, linha, coluna)

    def mouse_press_handler(_):
        copiar(config.copy_type, config.i, config.w)

    # Use type ignore para contornar o problema de tipagem
    label.mousePressEvent = mouse_press_handler  # type: ignore[method-assign]
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
    frame_dobra = QGroupBox()
    frame_dobra.setObjectName("sem_borda")
    frame_dobra.setFlat(True)
    frame_dobra.setStyleSheet("QGroupBox { margin-top: 0px; }")
    layout = QGridLayout(frame_dobra)
    layout.setContentsMargins(10, 0, 10, 0)
    layout.setSpacing(5)

    frame_dobra.setLayout(layout)

    _configurar_layout_dobra(layout)
    _criar_headers(layout)
    _criar_entradas_e_resultados(layout, w)
    _criar_labels_blank(layout, w)

    return frame_dobra


def _configurar_layout_dobra(layout):
    """Configura o layout com responsividade e espaçamento adequado."""
    # Configurar primeira coluna (labels de aba) com largura fixa
    layout.setColumnMinimumWidth(0, 50)
    layout.setColumnStretch(0, 0)

    # Configurar colunas de dados com expansão proporcional
    for col in range(1, 4):
        layout.setColumnStretch(col, 1)

    # Configurar espaçamento
    layout.setHorizontalSpacing(5)
    layout.setVerticalSpacing(3)


def _criar_headers(layout):
    """Cria os cabeçalhos das colunas com widgets auto-ajustáveis."""
    headers = ["Medida Ext.:", "Medida Dobra:", "Metade Dobra:"]

    for i, label_text in enumerate(headers):
        criar_label_header(layout, label_text, (0, i + 1))


def _criar_entradas_e_resultados(layout, w):
    """Cria as entradas e labels de resultado para cada aba."""
    for i in range(1, g.N):
        # Label da aba
        criar_label_aba(layout, f"Aba {i}:", (i, 0))

        # Entry para medida externa
        config_entry = ConfigEntry(
            layout=layout, nome_global=f"aba{i}_entry_{w}", pos=(i, 1), w=w, i=i
        )
        criar_entry_dobra(config_entry)

        # Label para medida da dobra
        config_medida = ConfigLabelResultado(
            layout=layout,
            nome_global=f"medidadobra{i}_label_{w}",
            pos=(i, 2),
            tooltip_text="Clique para copiar a medida da dobra.",
            i=i,
            w=w,
            copy_type="medida_dobra",
        )
        criar_label_resultado(config_medida)

        # Label para metade da dobra
        config_metade = ConfigLabelResultado(
            layout=layout,
            nome_global=f"metadedobra{i}_label_{w}",
            pos=(i, 3),
            tooltip_text="Clique para copiar a metade da dobra.",
            i=i,
            w=w,
            copy_type="metade_dobra",
        )
        criar_label_resultado(config_metade)


def _criar_labels_blank(layout, w):
    """Cria os labels do blank com widgets auto-ajustáveis."""
    # Label "Totais:"
    blank_label = QLabel("Totais:")
    blank_label.setObjectName("label_titulo")
    blank_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(blank_label, g.N + 1, 0, 1, 1)

    # Label da medida do blank (sobe para a mesma linha g.N+1, colunas 1-3)
    config_total_abas = ConfigLabelResultado(
        layout=layout,
        nome_global=f"total_abas_label_{w}",
        pos=(g.N + 1, 1),
        tooltip_text="Soma das medidas externas das abas.",
        i=g.N,
        w=w,
        copy_type="total_abas",
    )
    criar_label_resultado(config_total_abas)

    config_blank = ConfigLabelResultado(
        layout=layout,
        nome_global=f"medida_blank_label_{w}",
        pos=(g.N + 1, 2),
        tooltip_text="Clique para copiar a medida do blank.",
        i=g.N,
        w=w,
        copy_type="blank",
    )
    criar_label_resultado(config_blank)

    # Label da metade do blank
    config_metade_blank = ConfigLabelResultado(
        layout=layout,
        nome_global=f"metade_blank_label_{w}",
        pos=(g.N + 1, 3),
        tooltip_text="Clique para copiar a metade do blank.",
        i=g.N,
        w=w,
        copy_type="metade_blank",
    )
    criar_label_resultado(config_metade_blank)
