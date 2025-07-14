"""
Módulo para criar os botões e checkbuttons na interface gráfica.

Este módulo é responsável por criar os botões e checkbuttons que
serão exibidos na parte inferior da interface gráfica. Os botões
serão utilizados para manipular as dobras e a interface de forma
interativa.
"""

from PySide6.QtWidgets import QWidget, QGridLayout, QCheckBox, QPushButton, QApplication
from PySide6.QtCore import QTimer
from PySide6.QtCore import Qt
from src.utils.limpeza import limpar_dobras, limpar_tudo
from src.utils.janelas import cleanup_orphaned_windows
from src.utils.estilo import (
    obter_estilo_botao_vermelho,
    obter_estilo_botao_amarelo
)
from src.utils.interface import aplicar_medida_borda_espaco
import src.config.globals as g


class ExpansionManager:
    """Gerencia a expansão da interface de forma robusta"""

    def __init__(self):
        self.is_updating = False
        self.cleanup_timer = QTimer()
        self.cleanup_timer.setSingleShot(True)
        self.cleanup_timer.timeout.connect(self.force_cleanup_orphans)

    def force_cleanup_orphans(self):
        """Remove todas as janelas órfãs - usa função centralizada"""
        try:
            cleanup_orphaned_windows()
        except (ImportError, ValueError):
            pass

    def update_interface_size(self, exp_h, exp_v):
        """Atualiza o tamanho da interface baseado nos estados de expansão"""
        if self.is_updating or not g.PRINC_FORM:
            return

        self.is_updating = True
        try:
            self.force_cleanup_orphans()

            # Calcular novo tamanho baseado na expansão
            largura = 680 if exp_h else 340
            altura = 650 if exp_v else 500
            colunas = 2 if exp_h else 1
            num_abas = 10 if exp_v else 5

            # Atualizar estados globais
            g.EXP_H = exp_h
            g.EXP_V = exp_v
            g.VALORES_W = [1, 2] if exp_h else [1]

            print(
                f"Atualizando interface: {largura}x{altura}, {colunas} colunas, {num_abas} abas")

            # Aplicar setFixedSize para o tamanho atual
            g.PRINC_FORM.setFixedSize(largura, altura)

            # Recarregar interface se necessário
            if hasattr(g, 'CARREGAR_INTERFACE_FUNC') and callable(g.CARREGAR_INTERFACE_FUNC):
                g.CARREGAR_INTERFACE_FUNC(colunas, g.MAIN_LAYOUT)

            # Forçar limpeza completa do layout quando voltando ao estado normal
            if not exp_h and not exp_v:
                print("Estado normal detectado - aplicando ajustes básicos...")
                QTimer.singleShot(100, self._basic_layout_fix)

            # Forçar atualização do layout
            if g.MAIN_LAYOUT:
                g.MAIN_LAYOUT.invalidate()
                g.MAIN_LAYOUT.activate()

            # Processar eventos para garantir atualização visual
            app = QApplication.instance()
            if app:
                app.processEvents()

            # Restaurar configuração final após delay
            QTimer.singleShot(200, self._restore_limits)

            # Agendar limpeza de órfãos após mudanças
            self.cleanup_timer.start(300)

        except (ValueError, TypeError):
            print("Erro de valor ou tipo.")
        finally:
            self.is_updating = False

    def _basic_layout_fix(self):
        """Correção básica e conservadora para o layout no estado normal."""
        try:
            if not g.PRINC_FORM or not g.MAIN_LAYOUT:
                return

            print("Aplicando ajuste básico do layout...")

            # Apenas resetar a segunda coluna se ela existir
            g.MAIN_LAYOUT.setColumnStretch(1, 0)
            g.MAIN_LAYOUT.setColumnStretch(0, 1)

            # Forçar tamanho da janela
            g.PRINC_FORM.setFixedSize(340, 500)

            print("Ajuste básico aplicado!")

        except RuntimeError as e:
            print(f"Erro no ajuste básico: {e}")

    def _restore_limits(self):
        """Restaura configurações finais após mudanças de layout"""
        if not g.PRINC_FORM:
            return

        # Manter o tamanho fixo baseado no estado atual de expansão
        final_largura = 680 if g.EXP_H else 340
        final_altura = 650 if g.EXP_V else 500
        g.PRINC_FORM.setFixedSize(final_largura, final_altura)

        # Forçar reajuste completo do layout
        if g.MAIN_LAYOUT:
            g.MAIN_LAYOUT.invalidate()
            g.MAIN_LAYOUT.activate()
            g.MAIN_LAYOUT.update()

        # Atualizar widget central
        central_widget = g.PRINC_FORM.centralWidget()
        if central_widget:
            central_widget.updateGeometry()
            central_widget.adjustSize()

        # Processar eventos novamente
        app = QApplication.instance()
        if app:
            app.processEvents()


def criar_botoes():
    """
    Cria os botões e checkbuttons no frame inferior com nova lógica de expansão.
    """
    frame_botoes = QWidget()
    layout = QGridLayout(frame_botoes)

    # Configurar espaçamento e margens
    aplicar_medida_borda_espaco(layout)

    # Inicializar valores globais
    _inicializar_valores_globais()

    # Criar gerenciador de expansão
    expansion_manager = ExpansionManager()

    # Criar widgets
    widgets = _criar_widgets_botoes(expansion_manager)

    # Adicionar widgets ao layout
    _adicionar_widgets_ao_layout(layout, widgets)

    # Configurar estilos
    _configurar_estilos_botoes(widgets)

    # Configurar tooltips
    _configurar_tooltips(widgets)

    return frame_botoes


def _inicializar_valores_globais():
    """Inicializa valores globais se não existirem."""
    if not hasattr(g, 'EXP_V') or g.EXP_V is None:
        g.EXP_V = False
    if not hasattr(g, 'EXP_H') or g.EXP_H is None:
        g.EXP_H = False


def _criar_widgets_botoes(expansion_manager):
    """Cria todos os widgets dos botões."""
    widgets = {}

    # Checkbox para expandir vertical
    widgets['exp_v_check'] = _criar_checkbox_vertical(expansion_manager)

    # Checkbox para expandir horizontal
    widgets['exp_h_check'] = _criar_checkbox_horizontal(expansion_manager)

    # Botão para limpar dobras
    widgets['limpar_dobras_btn'] = _criar_botao_limpar_dobras()

    # Botão para limpar tudo
    widgets['limpar_tudo_btn'] = _criar_botao_limpar_tudo()

    return widgets


def _criar_checkbox_vertical(expansion_manager):
    """Cria o checkbox de expansão vertical."""
    exp_v_check = QCheckBox("Expandir Vertical")
    exp_v_check.setChecked(g.EXP_V)
    exp_v_check.setFixedHeight(20)

    def on_expandir_v(checked):
        """Callback para expansão vertical"""
        if not expansion_manager.is_updating:
            expansion_manager.update_interface_size(g.EXP_H, checked)

    exp_v_check.toggled.connect(on_expandir_v)
    return exp_v_check


def _criar_checkbox_horizontal(expansion_manager):
    """Cria o checkbox de expansão horizontal."""
    exp_h_check = QCheckBox("Expandir Horizontal")
    exp_h_check.setChecked(g.EXP_H)
    exp_h_check.setFixedHeight(20)

    def on_expandir_h(checked):
        """Callback para expansão horizontal"""
        if not expansion_manager.is_updating:
            expansion_manager.update_interface_size(checked, g.EXP_V)

    exp_h_check.toggled.connect(on_expandir_h)
    return exp_h_check


def _criar_botao_limpar_dobras():
    """Cria o botão para limpar dobras."""
    limpar_dobras_btn = QPushButton("🧹 Limpar Dobras")
    limpar_dobras_btn.clicked.connect(limpar_dobras)
    limpar_dobras_btn.setFixedHeight(20)
    return limpar_dobras_btn


def _criar_botao_limpar_tudo():
    """Cria o botão para limpar tudo."""
    limpar_tudo_btn = QPushButton("🗑️ Limpar Tudo")
    limpar_tudo_btn.clicked.connect(limpar_tudo)
    limpar_tudo_btn.setFixedHeight(20)
    return limpar_tudo_btn


def _adicionar_widgets_ao_layout(layout, widgets):
    """Adiciona os widgets ao layout."""
    layout.addWidget(widgets['exp_v_check'], 0, 0,
                     alignment=Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(widgets['exp_h_check'], 0, 1,
                     alignment=Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(widgets['limpar_dobras_btn'], 1, 0)
    layout.addWidget(widgets['limpar_tudo_btn'], 1, 1)


def _configurar_estilos_botoes(widgets):
    """Configura os estilos dos botões."""
    widgets['limpar_dobras_btn'].setStyleSheet(obter_estilo_botao_amarelo())
    widgets['limpar_tudo_btn'].setStyleSheet(obter_estilo_botao_vermelho())


def _configurar_tooltips(widgets):
    """Configura os tooltips dos widgets."""
    widgets['exp_v_check'].setToolTip("Expande a interface verticalmente")
    widgets['exp_h_check'].setToolTip("Expande a interface horizontalmente")
    widgets['limpar_dobras_btn'].setToolTip("Limpa as dobras")
    widgets['limpar_tudo_btn'].setToolTip("Limpa todos os valores")
