"""Formulário de Manual de Uso.

Este módulo apresenta instruções detalhadas de operação do aplicativo e oferece
um menu lateral no estilo sanduíche para navegar entre as categorias.
"""

from __future__ import annotations

import sys
from typing import Dict, Iterable, List, Optional, Tuple

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from src.components.barra_titulo import BarraTitulo
from src.forms.common import context_help
from src.forms.common.ui_helpers import configure_frameless_dialog
from src.utils.estilo import obter_tema_atual
from src.utils.janelas import Janela
from src.utils.utilitarios import ICON_PATH

Section = Tuple[str, str, str]

SECTION_KEYS_ORDER = (
    "main",
    "impressao",
    "comparar",
    "converter",
    "cadastro",
    "spring_back",
    "razao_rie",
    "autenticacao",
    "manual",
    "sobre",
    "admin",
)


def _create_section_widget(title: str, body: str) -> QWidget:
    """Cria o conteúdo visual de uma seção do manual."""
    container = QFrame()
    container.setObjectName("manualSectionContainer")
    container.setFrameShape(QFrame.Shape.StyledPanel)
    container.setStyleSheet(
        "#manualSectionContainer {"
        " border: 1px solid rgba(120, 120, 120, 80);"
        " border-radius: 8px;"
        " background-color: rgba(255, 255, 255, 8);"
        "}"
    )

    layout = QVBoxLayout(container)
    layout.setContentsMargins(18, 16, 18, 18)
    layout.setSpacing(12)

    header = QLabel(title)
    header_font = QFont()
    header_font.setPointSize(16)
    header_font.setBold(True)
    header.setFont(header_font)
    header.setAlignment(Qt.AlignmentFlag.AlignLeft)
    layout.addWidget(header)

    body_label = QLabel(body)
    body_label.setWordWrap(True)
    body_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
    body_label.setTextFormat(Qt.TextFormat.RichText)
    body_label.setOpenExternalLinks(True)
    body_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
    body_label.setMinimumHeight(120)
    layout.addWidget(body_label, 1)

    return container


def _format_help_message(message: str) -> str:
    """Ajusta o texto de ajuda para exibição em formato rich text."""
    return message


def _build_sections() -> Iterable[Section]:
    """Retorna conteúdo estruturado do manual."""
    for key, (title, message) in context_help.iter_help_entries(SECTION_KEYS_ORDER):
        yield key, title, _format_help_message(message)


class ManualDialog(QDialog):
    """Diálogo que apresenta o manual com navegação lateral."""

    # pylint: disable=R0915
    def __init__(
        self,
        parent: Optional[QWidget] = None,
        initial_key: Optional[str] = None,
    ) -> None:
        super().__init__(parent)
        self._keys: List[str] = []
        self._key_to_index: Dict[str, int] = {}
        self._current_key: Optional[str] = None

        self.setWindowTitle("Manual de Uso")
        self.setFixedSize(500, 513)
        configure_frameless_dialog(self, ICON_PATH)
        self.setModal(True)

        Janela.posicionar_janela(self, "centro")

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        barra = BarraTitulo(self, tema=obter_tema_atual())
        barra.titulo.setText("Manual de Uso")
        barra.set_help_callback(
            lambda: self.select_section_by_key("manual", ensure_menu_visible=True),
            "Dicas de navegação do manual",
        )
        root_layout.addWidget(barra)

        controle = QWidget()
        controle_layout = QVBoxLayout(controle)
        controle_layout.setContentsMargins(12, 12, 12, 12)
        controle_layout.setSpacing(8)

        self._menu_button = QToolButton()
        self._menu_button.setText("☰ Categorias")
        self._menu_button.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        self._menu_button.setCheckable(True)
        self._menu_button.setChecked(False)
        self._menu_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._menu_button.setToolTip("Abrir ou fechar o menu de categorias do manual")
        self._menu_button.toggled.connect(self._toggle_menu)
        controle_layout.addWidget(self._menu_button)

        root_layout.addWidget(controle)

        content_wrapper = QWidget()
        content_layout = QHBoxLayout(content_wrapper)
        content_layout.setContentsMargins(12, 0, 12, 12)
        content_layout.setSpacing(12)

        self._categoria_container = QFrame()
        self._categoria_container.setFrameShape(QFrame.Shape.StyledPanel)
        self._categoria_container.setVisible(False)
        self._categoria_container.setMinimumWidth(0)
        self._categoria_container.setMaximumWidth(0)

        categoria_layout = QVBoxLayout(self._categoria_container)
        categoria_layout.setContentsMargins(10, 10, 10, 10)
        categoria_layout.setSpacing(6)

        categoria_titulo = QLabel("Categorias")
        categoria_titulo.setAlignment(Qt.AlignmentFlag.AlignLeft)
        categoria_titulo.setStyleSheet("font-weight: bold; font-size: 13px;")
        categoria_layout.addWidget(categoria_titulo)

        self._category_list = QListWidget()
        self._category_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self._category_list.setUniformItemSizes(True)
        self._category_list.setSpacing(2)
        self._category_list.currentRowChanged.connect(self._on_category_changed)
        categoria_layout.addWidget(self._category_list, 1)
        categoria_layout.addStretch(1)

        content_layout.addWidget(self._categoria_container)

        self._stack = QStackedWidget()
        self._stack.setContentsMargins(0, 0, 0, 0)
        content_layout.addWidget(self._stack, 1)

        root_layout.addWidget(content_wrapper)

        self._populate_sections()

        default_key = initial_key if initial_key in self._key_to_index else None
        if default_key is None and self._keys:
            default_key = self._keys[0]

        if default_key:
            self.select_section_by_key(default_key)

    def _populate_sections(self) -> None:
        for key, title, body in _build_sections():
            self._append_section(key, title, body)

    def _append_section(self, key: str, title: str, body: str) -> None:
        item = QListWidgetItem(title)
        item.setData(Qt.ItemDataRole.UserRole, key)
        item.setToolTip(title)
        self._category_list.addItem(item)

        section_widget = _create_section_widget(title, body)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setWidget(section_widget)
        self._stack.addWidget(scroll)

        index = self._stack.count() - 1
        self._keys.append(key)
        self._key_to_index[key] = index

    def _toggle_menu(self, checked: bool) -> None:
        self._categoria_container.setVisible(checked)
        target_width = 240 if checked else 0
        self._categoria_container.setMinimumWidth(target_width)
        self._categoria_container.setMaximumWidth(target_width)
        self._menu_button.setText("✖ Fechar categorias" if checked else "☰ Categorias")

    def _on_category_changed(self, row: int) -> None:
        if row < 0 or row >= self._stack.count():
            return
        if self._stack.currentIndex() != row:
            self._stack.setCurrentIndex(row)

        item = self._category_list.item(row)
        if item:
            key = item.data(Qt.ItemDataRole.UserRole)
            self._current_key = str(key) if key is not None else None

    def select_section_by_key(
        self, key: str, *, ensure_menu_visible: bool = False
    ) -> None:
        """Seleciona uma seção do manual pelo seu identificador."""
        index = self._key_to_index.get(key)
        if index is None:
            return

        if ensure_menu_visible and not self._menu_button.isChecked():
            self._menu_button.setChecked(True)

        if self._stack.currentIndex() != index:
            self._stack.setCurrentIndex(index)

        if self._category_list.currentRow() != index:
            self._category_list.blockSignals(True)
            self._category_list.setCurrentRow(index)
            self._category_list.blockSignals(False)

        self._current_key = key

        current_item = self._category_list.item(index)
        if current_item:
            self._category_list.scrollToItem(
                current_item, QListWidget.ScrollHint.PositionAtCenter
            )


def show_manual(
    root: Optional[QWidget],
    initial_key: Optional[str] = None,
    *,
    block: bool = False,
) -> ManualDialog:
    """Exibe o manual, opcionalmente destacando uma seção específica."""

    dialog = ManualDialog(root, initial_key)

    if block:
        dialog.exec()
    else:
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    return dialog


context_help.register_manual_launcher(
    lambda parent, key, block: show_manual(parent, key, block=block)
)


def main(root: Optional[QWidget]) -> ManualDialog:
    """Compatibilidade com chamadas existentes que abrem o manual."""

    return show_manual(root, block=False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    _dialog = main(None)
    sys.exit(app.exec())
