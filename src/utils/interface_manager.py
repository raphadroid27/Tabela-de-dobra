"""
Módulo para gerenciar a interface principal do aplicativo.
Sistema robusto com gerenciamento seguro de widgets.
"""

import logging

from PySide6.QtWidgets import QApplication

from src.components import botoes
from src.components.avisos import avisos
from src.components.cabecalho import cabecalho
from src.components.dobra_90 import dobras
from src.config import globals as g
from src.utils.interface import calcular_valores, todas_funcoes
from src.utils.utilitarios import WIDGET_CABECALHO, tem_configuracao_dobras_valida
from src.utils.widget import widget_state_manager


def safe_process_events():
    """Processa eventos de forma segura."""
    app = QApplication.instance()
    if app:
        app.processEvents()


def safe_clear_layout(layout):
    """Limpa um layout de forma segura, deletando widgets adequadamente."""
    if not hasattr(layout, "count"):
        return

    items_to_remove = []
    while layout.count():
        item = layout.takeAt(0)
        if item:
            items_to_remove.append(item)

    for item in items_to_remove:
        if item:
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.hide()
                widget.deleteLater()
    safe_process_events()


def clear_global_widget_references():
    """Limpa referências globais de widgets antes da recriação."""
    widget_names = WIDGET_CABECALHO.copy()
    if tem_configuracao_dobras_valida():
        for w in g.VALORES_W:
            for i in range(1, 11):
                widget_names.extend(
                    [
                        f"aba{i}_entry_{w}",
                        f"medidadobra{i}_label_{w}",
                        f"metadedobra{i}_label_{w}",
                    ]
                )
            widget_names.extend([f"medida_blank_label_{w}", f"metade_blank_label_{w}"])

    for widget_name in widget_names:
        if hasattr(g, widget_name):
            setattr(g, widget_name, None)


def carregar_interface(var, layout):
    """Atualiza e recria os widgets no layout com base no valor de var."""
    if not g.PRINC_FORM:
        return

    try:
        g.PRINC_FORM.setUpdatesEnabled(False)
        g.INTERFACE_RELOADING = True

        _preparar_interface_reload(layout)
        _criar_widgets_interface(var, layout)
        _configurar_layout_interface(layout)
        _finalizar_interface_reload()

    except RuntimeError as e:
        _tratar_erro_interface_reload(e)
    finally:
        if g.PRINC_FORM:
            g.PRINC_FORM.setUpdatesEnabled(True)
            g.PRINC_FORM.repaint()
            app = QApplication.instance()
            if app:
                app.processEvents()
        g.INTERFACE_RELOADING = False


def _preparar_interface_reload(layout):
    """Prepara a interface para recarregamento."""
    if hasattr(g, "MAT_COMB") and g.MAT_COMB is not None:
        widget_state_manager.capture_current_state()

    safe_clear_layout(layout)
    clear_global_widget_references()
    safe_process_events()


def _criar_widgets_interface(var, layout):
    """Cria os widgets da interface."""
    layout.addWidget(cabecalho(), 0, 0)
    if var == 2:
        layout.addWidget(avisos(), 0, 1)

    num_abas = 10 if g.EXP_V else 5
    g.N = num_abas + 1

    for i, w_val in enumerate(g.VALORES_W):
        layout.addWidget(dobras(w_val), 1, i)

    layout.addWidget(botoes.criar_botoes(), 2, 0, 1, len(g.VALORES_W))


def _configurar_layout_interface(layout):
    """Configura o layout da interface."""
    layout.setRowStretch(0, 0)
    layout.setRowStretch(1, 1)
    layout.setRowStretch(2, 0)
    layout.setSpacing(0)
    layout.setContentsMargins(0, 0, 0, 0)
    for col in range(layout.columnCount()):
        layout.setColumnStretch(col, 0 if col > len(g.VALORES_W) - 1 else 1)


def _finalizar_interface_reload():
    """Finaliza o recarregamento da interface."""
    widget_state_manager.disable()
    try:
        todas_funcoes()
    except RuntimeError as e:
        logging.error("Erro ao executar todas as funções: %s", e, exc_info=True)
    finally:
        widget_state_manager.enable()

    widget_state_manager.restore_widget_state()
    calcular_valores()


def _tratar_erro_interface_reload(e):
    """Trata erros durante o recarregamento da interface."""
    widget_state_manager.enable()
    g.INTERFACE_RELOADING = False
    logging.critical("ERRO CRÍTICO no carregamento da interface: %s", e, exc_info=True)
