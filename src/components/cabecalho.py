"""Cabeçalho da interface com campos de entrada e rótulos."""

from PySide6.QtCore import QLocale, Qt
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import QComboBox, QGridLayout, QGroupBox, QLabel, QLineEdit

from src.config import globals as g
from src.utils.estilo import (
    ALTURA_PADRAO_COMPONENTE,
    LARGURA_MINIMA_COMPONENTE,
    aplicar_estilo_widget_auto_ajustavel,
    configurar_layout_flexivel,
)
from src.utils.interface import (
    WidgetUpdater,
)
from src.utils.interface import calcular_valores_debounced as calcular_valores
from src.utils.interface import (
    canal_tooltip,
    copiar,
)


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
    label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    layout.addWidget(label, linha, coluna)
    return label


def criar_widget_cabecalho(layout, tipo, nome_global, pos, **kwargs):
    """
    Cria widgets do cabeçalho com largura auto-ajustável.

    Mantém altura fixa mas permite largura flexível.

    Args:
        layout: Layout onde o widget será adicionado.
        tipo: Tipo do widget ('label', 'combobox', 'entry').
        nome_global: Nome do atributo global para armazenar o widget.
        pos: Posição no layout.
        **kwargs: Argumentos adicionais para o widget.

    Returns:
        Widget criado e adicionado ao layout.
    """
    if tipo == "label":
        widget = QLabel(kwargs.pop("text", ""))
        widget.setFrameShape(QLabel.Shape.Panel)
        widget.setFrameShadow(QLabel.Shadow.Sunken)
        widget.setFixedHeight(ALTURA_PADRAO_COMPONENTE)
        widget.setMinimumWidth(LARGURA_MINIMA_COMPONENTE)
        widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
    elif tipo == "combobox":
        widget = QComboBox(**kwargs)
        widget.setFixedHeight(ALTURA_PADRAO_COMPONENTE)
        widget.setMinimumWidth(LARGURA_MINIMA_COMPONENTE)
        aplicar_estilo_widget_auto_ajustavel(widget, "combobox")
    elif tipo == "entry":
        widget = QLineEdit(**kwargs)
        widget.setFixedHeight(ALTURA_PADRAO_COMPONENTE)
        widget.setMinimumWidth(LARGURA_MINIMA_COMPONENTE)
        widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        aplicar_estilo_widget_auto_ajustavel(widget, "lineedit")
    else:
        return None

    layout.addWidget(widget, *pos)
    setattr(g, nome_global, widget)
    return widget


def criar_widget_observacao(layout, nome_global, pos, **kwargs):
    """
    Cria widget de observação (comportamento original, SEM alterações).

    Mantém largura flexível para ocupar toda a área disponível.

    Args:
        layout: Layout onde o widget será adicionado.
        nome_global: Nome do atributo global para armazenar o widget.
        pos: Posição no layout.
        **kwargs: Argumentos adicionais para o widget.

    Returns:
        Widget de observação criado.
    """
    widget = QLabel(kwargs.pop("text", ""))
    widget.setFrameShape(QLabel.Shape.Panel)
    widget.setFrameShadow(QLabel.Shadow.Sunken)
    widget.setFixedHeight(ALTURA_PADRAO_COMPONENTE)
    widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

    layout.addWidget(widget, *pos)
    setattr(g, nome_global, widget)
    return widget


def _criar_linha_1(layout):
    """Cria a primeira linha do cabeçalho com Material, Espessura, Canal e Comprimento."""
    criar_label(layout, "Material:", (0, 0))
    criar_label(layout, "Espessura:", (0, 1))
    criar_label(layout, "Canal:", (0, 2))
    criar_label(layout, "Compr.:", (0, 3))

    mat_comb = criar_widget_cabecalho(layout, "combobox", "MAT_COMB", (1, 0))
    esp_comb = criar_widget_cabecalho(layout, "combobox", "ESP_COMB", (1, 1))
    canal_comb = criar_widget_cabecalho(layout, "combobox", "CANAL_COMB", (1, 2))
    compr_entry = criar_widget_cabecalho(layout, "entry", "COMPR_ENTRY", (1, 3))
    # Validador numérico (aceita vírgula conforme locale PT-BR)
    val_c = QDoubleValidator(0.0, 999999.0, 3)
    val_c.setNotation(QDoubleValidator.Notation.StandardNotation)
    val_c.setLocale(QLocale(QLocale.Language.Portuguese, QLocale.Country.Brazil))
    compr_entry.setValidator(val_c)

    # Tooltips
    mat_comb.setToolTip("Selecione o material para a dobra.")
    esp_comb.setToolTip("Selecione a espessura do material.")
    canal_comb.setToolTip("Selecione o canal de dobra.")
    compr_entry.setToolTip("Digite o comprimento da peça em milímetros.")

    # Conectar eventos
    compr_entry.textChanged.connect(calcular_valores)  # Debounce durante digitação
    compr_entry.editingFinished.connect(
        lambda: calcular_valores(0)
    )  # Instantâneo ao finalizar
    canal_comb.currentTextChanged.connect(
        lambda: calcular_valores(10)
    )  # Rápido para combobox (10ms delay)

    return mat_comb, esp_comb, canal_comb, compr_entry


def _criar_linha_2(layout):
    """Cria a segunda linha do cabeçalho com Raio Interno, Fator K, Dedução e Offset."""
    criar_label(layout, "Raio Interno:", (2, 0))
    criar_label(layout, "Fator K:", (2, 1))
    criar_label(layout, "Dedução:", (2, 2))
    criar_label(layout, "Offset:", (2, 3))

    ri_entry = criar_widget_cabecalho(layout, "entry", "RI_ENTRY", (3, 0))
    # Validador numérico (aceita vírgula conforme locale PT-BR)
    val_r = QDoubleValidator(0.0, 999999.0, 3)
    val_r.setNotation(QDoubleValidator.Notation.StandardNotation)
    val_r.setLocale(QLocale(QLocale.Language.Portuguese, QLocale.Country.Brazil))
    ri_entry.setValidator(val_r)
    k_lbl = criar_widget_cabecalho(layout, "label", "K_LBL", (3, 1))
    ded_lbl = criar_widget_cabecalho(layout, "label", "DED_LBL", (3, 2))
    offset_lbl = criar_widget_cabecalho(layout, "label", "OFFSET_LBL", (3, 3))

    # Tooltips
    ri_entry.setToolTip("Digite o raio interno da dobra em milímetros.")
    ded_lbl.setToolTip(
        "Dedução de dobra calculada com base no material, espessura e canal. Clique para copiar."
    )
    offset_lbl.setToolTip(
        "Offset calculado com base no raio interno. Clique para copiar."
    )

    # Conectar eventos
    ri_entry.textChanged.connect(calcular_valores)  # Debounce durante digitação
    ri_entry.editingFinished.connect(
        lambda: calcular_valores(0)
    )  # Instantâneo ao finalizar
    k_lbl.mousePressEvent = lambda event: copiar("fator_k")
    ded_lbl.mousePressEvent = lambda event: copiar("dedução")
    offset_lbl.mousePressEvent = lambda event: copiar("offset")

    return ri_entry, k_lbl, ded_lbl, offset_lbl


def _criar_linha_3(layout):
    """Cria a terceira linha do cabeçalho com Ded. Espec., Aba Mín., Ext. Z90° e Força."""
    criar_label(layout, "Ded. Espec.:", (4, 0))
    criar_label(layout, "Aba Mín.:", (4, 1))
    criar_label(layout, 'Ext. "Z" 90°:', (4, 2))
    criar_label(layout, "Força (t/m):", (4, 3))

    ded_espec_entry = criar_widget_cabecalho(layout, "entry", "DED_ESPEC_ENTRY", (5, 0))
    aba_ext_lbl = criar_widget_cabecalho(layout, "label", "ABA_EXT_LBL", (5, 1))
    z_ext_lbl = criar_widget_cabecalho(layout, "label", "Z_EXT_LBL", (5, 2))
    forca_lbl = criar_widget_cabecalho(layout, "label", "FORCA_LBL", (5, 3))

    # Tooltips
    ded_espec_entry.setToolTip(
        "Digite uma dedução específica em milímetros para sobrescrever a calculada."
    )
    aba_ext_lbl.setToolTip(
        "Medida mínima externa da aba do perfil dobrado considerando ângulo de 90°."
    )
    z_ext_lbl.setToolTip(
        'Medida mínima externa da altura de um perfil "Z" considerando ângulos de 90°.'
    )
    forca_lbl.setToolTip("Força necessária para a dobra em toneladas por metro (t/m).")

    # Conectar eventos
    ded_espec_entry.textChanged.connect(calcular_valores)  # Debounce durante digitação
    ded_espec_entry.editingFinished.connect(
        lambda: calcular_valores(0)
    )  # Instantâneo ao finalizar

    return ded_espec_entry, aba_ext_lbl, z_ext_lbl, forca_lbl


def _criar_observacoes(layout):
    """
    Cria a seção de observações (MANTIDA EXATAMENTE COMO ESTAVA).

    Preserva comportamento original com largura flexível.
    """
    obs_label = criar_label(layout, "Observações:", (6, 0))
    layout.addWidget(obs_label, 6, 0, 1, 4)

    # USA função específica para observações (comportamento original)
    obs_widget = criar_widget_observacao(layout, "OBS_LBL", (7, 0))
    # Span de 4 colunas (largura total)
    layout.addWidget(obs_widget, 7, 0, 1, 4)
    obs_widget.setToolTip("Observações sobre a dobra, material ou canal selecionado.")


def _conectar_eventos(mat_comb, esp_comb, canal_comb, compr_entry):
    """Conecta os eventos dos widgets principais."""
    if mat_comb:
        mat_comb.currentTextChanged.connect(
            lambda: WidgetUpdater().atualizar("espessura")
        )

    if esp_comb:
        esp_comb.currentTextChanged.connect(lambda: WidgetUpdater().atualizar("canal"))

    if canal_comb:
        canal_comb.currentTextChanged.connect(
            lambda: WidgetUpdater().atualizar("dedução")
        )
        canal_comb.currentTextChanged.connect(canal_tooltip)

    if compr_entry:
        compr_entry.textChanged.connect(calcular_valores)

    canal_tooltip()


def cabecalho():
    """
    Monta o cabeçalho da interface gráfica com widgets auto-ajustáveis.

    Features:
    - Widgets com altura fixa mas largura flexível
    - Observações mantidas com comportamento original
    - Layout responsivo que se adapta ao conteúdo
    - Distribuição proporcional do espaço disponível

    Returns:
        QGroupBox contendo o cabeçalho completo.
    """
    frame_cabecalho = QGroupBox()
    frame_cabecalho.setFlat(True)
    frame_cabecalho.setStyleSheet("QGroupBox { margin-top: 0px; }")
    layout = QGridLayout(frame_cabecalho)
    layout.setContentsMargins(10, 0, 10, 0)
    layout.setSpacing(5)

    configurar_layout_flexivel(layout)

    mat_comb, esp_comb, canal_comb, compr_entry = _criar_linha_1(layout)
    _criar_linha_2(layout)
    _criar_linha_3(layout)
    _criar_observacoes(layout)

    _conectar_eventos(mat_comb, esp_comb, canal_comb, compr_entry)

    return frame_cabecalho
