"""Funções utilitárias compartilhadas entre os formulários."""

from __future__ import annotations

from typing import Iterable

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QHBoxLayout,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.utils.janelas import Janela
from src.utils.utilitarios import aplicar_medida_borda_espaco


def configure_frameless_dialog(dialog: QWidget, icon_path: str) -> None:
    """Aplica configuração padrão de janelas com barra de título nativa."""
    dialog.setWindowFlags(Qt.WindowType.Window | Qt.WindowMinimizeButtonHint |
                          Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
    if Janela.get_on_top_state():
        dialog.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
    dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
    dialog.setWindowIcon(QIcon(icon_path))


def create_dialog_scaffold(
    dialog: QWidget,
    *,
    title: str,
    size: tuple[int, int],
    icon_path: str,
    **options,
) -> QVBoxLayout:
    """Configura o esqueleto base de diálogos com barra de título nativa."""
    position = options.get("position")
    barra_title = options.get("barra_title")

    dialog.setWindowTitle(barra_title or title)
    dialog.setMinimumSize(*size)
    configure_frameless_dialog(dialog, icon_path)
    Janela.posicionar_janela(dialog, position)

    layout = QVBoxLayout(dialog)
    aplicar_medida_borda_espaco(layout, 0)

    return layout


def attach_actions_with_progress(
    main_layout: QVBoxLayout,
    action_layout: QHBoxLayout,
) -> QProgressBar:
    """Anexa o layout de ações ao principal e adiciona uma barra de progresso ocultada."""
    main_layout.addLayout(action_layout)
    progress_bar = QProgressBar()
    progress_bar.setVisible(False)
    main_layout.addWidget(progress_bar)
    return progress_bar


def update_processing_state(
    is_running: bool,
    widgets_to_toggle: Iterable[QWidget],
    cancel_button: QPushButton,
    progress_bar: QProgressBar,
) -> None:
    """Atualiza o estado de execução da UI durante operações assíncronas."""
    for widget in widgets_to_toggle:
        widget.setEnabled(not is_running)

    cancel_button.setEnabled(is_running)
    if not is_running:
        cancel_button.setText("🛑 Cancelar")

    progress_bar.setVisible(is_running)
    if is_running:
        progress_bar.setValue(0)


def request_worker_cancel(worker, cancel_button: QPushButton) -> None:
    """Solicita o cancelamento seguro de um worker assíncrono."""
    if worker:
        cancel_button.setText("Aguarde...")
        cancel_button.setEnabled(False)
        worker.stop()


def stop_worker_on_error(worker, cancel_button: QPushButton | None = None) -> None:
    """Garante que o worker seja interrompido em caso de erro."""
    if worker:
        worker.stop()
        if cancel_button:
            cancel_button.setText("🛑 Cancelar")
            cancel_button.setEnabled(True)
