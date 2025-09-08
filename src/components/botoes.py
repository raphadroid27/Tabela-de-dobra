"""
Módulo para criar os botões e checkbuttons na interface gráfica.

Este módulo é responsável por criar os botões e checkbuttons que
serão exibidos na parte inferior da interface gráfica. Os botões
serão utilizados para manipular as dobras e a interface de forma
interativa.
"""

import logging

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QCheckBox, QGridLayout, QPushButton, QWidget

import src.config.globals as g
from src.utils.estilo import aplicar_estilo_botao, aplicar_estilo_checkbox
from src.utils.interface import calcular_valores_debounced, limpar_dobras, limpar_tudo
from src.utils.janelas import Janela

# Constantes para dimensões da interface
LARGURA_CONTRAIDA = 360
ALTURA_CONTRAIDA = 513
LARGURA_EXPANDIDA = 720
ALTURA_EXPANDIDA = 650
COLUNAS_CONTRAIDA = 1
COLUNAS_EXPANDIDA = 2


class ExpansionManager:
    """Gerencia a expansão da interface de forma robusta."""

    def __init__(self):
        """Inicializa o gerenciador de expansão."""
        self.is_updating = False
        self.cleanup_timer = QTimer()
        self.cleanup_timer.setSingleShot(True)
        self.cleanup_timer.timeout.connect(self.force_cleanup_orphans)

    def force_cleanup_orphans(self):
        """Remove todas as janelas órfãs utilizando a função centralizada."""
        try:
            Janela.remover_janelas_orfas()
        except (ImportError, ValueError, RuntimeError) as exc:
            logging.debug("Falha ao limpar janelas órfãs: %s", exc)

    def update_interface_size(self, exp_h, exp_v):
        """Atualiza o tamanho da interface conforme os estados de expansão."""
        if self.is_updating or not g.PRINC_FORM:
            return

        self.is_updating = True
        try:
            # Calcular novo tamanho baseado na expansão
            largura = LARGURA_EXPANDIDA if exp_h else LARGURA_CONTRAIDA
            altura = ALTURA_EXPANDIDA if exp_v else ALTURA_CONTRAIDA
            colunas = COLUNAS_EXPANDIDA if exp_h else COLUNAS_CONTRAIDA

            # Atualizar estados globais
            g.EXP_H = exp_h
            g.EXP_V = exp_v
            g.VALORES_W = [1, 2] if exp_h else [1]

            logging.info(
                "Atualizando interface para: %dx%d, %d colunas",
                largura,
                altura,
                colunas,
            )

            # Evitar travar tamanho: manter mínimo e permitir resize
            try:
                g.PRINC_FORM.setMinimumSize(largura, altura)
                g.PRINC_FORM.resize(largura, altura)
            except (AttributeError, RuntimeError, TypeError, ValueError) as exc:
                logging.debug("Falha ao redimensionar janela principal: %s", exc)

            if hasattr(g, "CARREGAR_INTERFACE_FUNC") and callable(
                g.CARREGAR_INTERFACE_FUNC
            ):
                g.CARREGAR_INTERFACE_FUNC(colunas, g.MAIN_LAYOUT)

            # Processa eventos pendentes do Qt para estabilizar o layout
            app = QApplication.instance()
            if app:
                app.processEvents()

            # Dispara recálculo debounced após relayout para refletir corretamente os widgets
            try:
                calcular_valores_debounced(0)
            except (AttributeError, ValueError, RuntimeError, TypeError) as exc:
                # salvaguarda para não quebrar a UI em cenários inesperados
                logging.debug("Recálculo debounced pós-relayout falhou: %s", exc)

            # Agendar limpeza de órfãos após mudanças (mantido por segurança)
            self.cleanup_timer.start(500)

        except (ValueError, TypeError, RuntimeError) as e:
            logging.error("Erro ao atualizar o tamanho da interface: %s", e)
        finally:
            self.is_updating = False


def criar_botoes():
    """Cria botões e checkbuttons no frame inferior com lógica de expansão."""
    frame_botoes = QWidget()
    layout = QGridLayout(frame_botoes)
    layout.setContentsMargins(10, 0, 10, 10)
    layout.setSpacing(5)

    _inicializar_valores_globais()

    expansion_manager = ExpansionManager()

    widgets = _criar_widgets_botoes(expansion_manager)

    _adicionar_widgets_ao_layout(layout, widgets)

    _configurar_estilos_botoes(widgets)

    _configurar_tooltips(widgets)

    return frame_botoes


def _inicializar_valores_globais():
    """Inicializa valores globais se não existirem."""
    if not hasattr(g, "EXP_V") or g.EXP_V is None:
        g.EXP_V = False
    if not hasattr(g, "EXP_H") or g.EXP_H is None:
        g.EXP_H = False


def _criar_widgets_botoes(expansion_manager):
    """Cria todos os widgets dos botões."""
    widgets = {}

    # Checkbox para expandir vertical
    widgets["exp_v_check"] = _criar_checkbox_vertical(expansion_manager)

    # Checkbox para expandir horizontal
    widgets["exp_h_check"] = _criar_checkbox_horizontal(expansion_manager)

    # Botão para limpar dobras
    widgets["limpar_dobras_btn"] = _criar_botao_limpar_dobras()

    # Botão para limpar tudo
    widgets["limpar_tudo_btn"] = _criar_botao_limpar_tudo()

    return widgets


def _criar_checkbox_vertical(expansion_manager):
    """Cria o checkbox de expansão vertical."""
    exp_v_check = QCheckBox("Expandir Vertical")
    exp_v_check.setChecked(bool(g.EXP_V))
    aplicar_estilo_checkbox(exp_v_check)
    exp_v_check.setShortcut("Alt+V")
    exp_v_check.setAccessibleName("Expansão Vertical")
    exp_v_check.setStatusTip("Alternar expansão vertical (Alt+V)")

    def on_expandir_v(checked):
        """Alterne a expansão vertical."""
        if not expansion_manager.is_updating:
            expansion_manager.update_interface_size(g.EXP_H, checked)

    exp_v_check.toggled.connect(on_expandir_v)
    return exp_v_check


def _criar_checkbox_horizontal(expansion_manager):
    """Cria o checkbox de expansão horizontal."""
    exp_h_check = QCheckBox("Expandir Horizontal")
    exp_h_check.setChecked(bool(g.EXP_H))
    aplicar_estilo_checkbox(exp_h_check)
    exp_h_check.setShortcut("Alt+H")
    exp_h_check.setAccessibleName("Expansão Horizontal")
    exp_h_check.setStatusTip("Alternar expansão horizontal (Alt+H)")

    def on_expandir_h(checked):
        """Alterne a expansão horizontal."""
        if not expansion_manager.is_updating:
            expansion_manager.update_interface_size(checked, g.EXP_V)

    exp_h_check.toggled.connect(on_expandir_h)
    return exp_h_check


def _criar_botao_limpar_dobras():
    """Cria o botão para limpar dobras."""
    limpar_dobras_btn = QPushButton("🧹 Limpar Dobras")
    # Estilo aplicado centralmente em _configurar_estilos_botoes
    limpar_dobras_btn.setShortcut("Ctrl+D")
    limpar_dobras_btn.setAccessibleName("Limpar Dobras")
    limpar_dobras_btn.setStatusTip("Limpar somente as dobras (Ctrl+D)")
    limpar_dobras_btn.clicked.connect(limpar_dobras)
    return limpar_dobras_btn


def _criar_botao_limpar_tudo():
    """Cria o botão para limpar tudo."""
    limpar_tudo_btn = QPushButton("🗑️ Limpar Tudo")
    # Estilo aplicado centralmente em _configurar_estilos_botoes
    limpar_tudo_btn.setShortcut("Ctrl+L")
    limpar_tudo_btn.setAccessibleName("Limpar Tudo")
    limpar_tudo_btn.setStatusTip("Limpar todos os valores (Ctrl+L)")
    limpar_tudo_btn.clicked.connect(limpar_tudo)
    return limpar_tudo_btn


def _adicionar_widgets_ao_layout(layout, widgets):
    """Adiciona os widgets ao layout."""
    layout.addWidget(
        widgets["exp_v_check"], 0, 0, alignment=Qt.AlignmentFlag.AlignCenter
    )
    layout.addWidget(
        widgets["exp_h_check"], 0, 1, alignment=Qt.AlignmentFlag.AlignCenter
    )
    layout.addWidget(widgets["limpar_dobras_btn"], 1, 0)
    layout.addWidget(widgets["limpar_tudo_btn"], 1, 1)


def _configurar_estilos_botoes(widgets):
    """Configura os estilos dos botões."""
    aplicar_estilo_botao(widgets["limpar_dobras_btn"], "amarelo")
    aplicar_estilo_botao(widgets["limpar_tudo_btn"], "vermelho")


def _configurar_tooltips(widgets):
    """Configura os tooltips dos widgets."""
    widgets["exp_v_check"].setToolTip("Expande a interface verticalmente")
    widgets["exp_h_check"].setToolTip("Expande a interface horizontalmente")
    widgets["limpar_dobras_btn"].setToolTip("Limpa as dobras")
    widgets["limpar_tudo_btn"].setToolTip("Limpa todos os valores")
