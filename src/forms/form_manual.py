"""Formulário de Manual de Uso.

Este módulo apresenta instruções detalhadas de operação do aplicativo e oferece
um menu lateral no estilo sanduíche para navegar entre as categorias.
"""

from __future__ import annotations

import sys
from typing import Dict, Iterable, Optional, Tuple

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QTextDocument
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
    QTextBrowser,
    QSizePolicy,
    QWidget,
)

from src.forms.common import context_help
from src.forms.common.ui_helpers import configurar_dialogo_padrao
from src.utils.utilitarios import ICON_PATH, aplicar_medida_borda_espaco

Section = Tuple[str, str, str]

ALTURA_FORM_PADRAO = 510
LARGURA_FORM_PADRAO = 500

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


_manual_instance: ManualDialog | None = None


def _create_section_widget(title: str, body: str) -> QWidget:
    """Cria o conteúdo visual de uma seção do manual."""
    container = QWidget()
    container.setObjectName("container_manual")

    layout = QVBoxLayout(container)
    layout.setContentsMargins(5, 0, 0, 5)
    layout.setSpacing(0)

    header = QLabel(title)
    header.setObjectName("label_titulo_h4")

    layout.addWidget(header, 1)

    body_widget = QTextBrowser()
    body_widget.setHtml(body)
    body_widget.setOpenExternalLinks(True)
    body_widget.setReadOnly(True)
    body_widget.setFrameShape(QFrame.Shape.NoFrame)
    body_widget.setSizePolicy(
        QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
    )
    layout.addWidget(body_widget, 1)

    return container


def _clean_section_title(title: str) -> str:
    if "<" not in title and ">" not in title:
        return title.strip()
    doc = QTextDocument()
    doc.setHtml(title)
    return doc.toPlainText().strip()


def _build_sections() -> Iterable[Section]:
    """Gera tuplas (key, title, body) das seções do manual na ordem desejada."""
    for key, (title, message) in context_help.iter_help_entries(
        SECTION_KEYS_ORDER, include_missing=False
    ):
        # Retornamos a mensagem diretamente; caso futuro exija transformação,
        # inserir aqui (ex.: sanitização ou conversão markdown->HTML).
        yield key, title, message


class _ContentClickFilter(QObject):
    def __init__(self, dialog: "ManualDialog") -> None:
        super().__init__(dialog)
        self._dialog = dialog

    def eventFilter(self, obj, event):  # pylint: disable=C0103
        """Intercepta cliques no conteúdo para recolher o menu de categorias."""
        if event.type() == QEvent.Type.MouseButtonPress:
            self._dialog.collapse_menu_on_content_click()
        return super().eventFilter(obj, event)


class ManualDialog(QDialog):
    """Diálogo que apresenta o manual com navegação lateral."""

    # pylint: disable=R0915
    def __init__(
        self,
        parent: Optional[QWidget] = None,
        initial_key: Optional[str] = None,
    ) -> None:
        super().__init__(parent)
        self._key_to_index: Dict[str, int] = {}
        self.setWindowTitle("Manual de Uso")
        self.setMinimumSize(LARGURA_FORM_PADRAO, ALTURA_FORM_PADRAO)
        configurar_dialogo_padrao(self, ICON_PATH)
        self.setModal(False)
        self.setWindowModality(Qt.WindowModality.NonModal)
        self._content_click_filter = _ContentClickFilter(self)

        root_layout = QVBoxLayout(self)
        aplicar_medida_borda_espaco(root_layout, 0, 0)

        controle = QWidget()
        controle_layout = QVBoxLayout(controle)
        controle_layout.setContentsMargins(10, 5, 0, 0)
        controle_layout.setSpacing(0)

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
        content_layout.setContentsMargins(10, 5, 10, 10)
        content_layout.setSpacing(0)

        self._categoria_container = QWidget()
        self._categoria_container.setVisible(False)
        self._categoria_container.setMinimumWidth(0)
        self._categoria_container.setMaximumWidth(0)

        categoria_layout = QVBoxLayout(self._categoria_container)
        categoria_layout.setContentsMargins(0, 0, 5, 0)
        categoria_layout.setSpacing(0)

        self._category_list = QListWidget()
        self._category_list.setObjectName("lista_categoria")
        self._category_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self._category_list.setUniformItemSizes(True)
        aplicar_medida_borda_espaco(self._category_list, 0, 0)
        self._category_list.currentRowChanged.connect(self._on_category_changed)
        _font = self._category_list.font()
        _font.setPointSize(10)
        _font.setBold(True)
        self._category_list.setFont(_font)
        categoria_layout.addWidget(self._category_list)

        content_layout.addWidget(self._categoria_container)

        self._stack = QStackedWidget()
        content_layout.addWidget(self._stack, 1)

        root_layout.addWidget(content_wrapper)

        self._populate_sections()

        default_key = initial_key if initial_key in self._key_to_index else None
        if default_key is None and self._category_list.count() > 0:
            first_item = self._category_list.item(0)
            if first_item is not None:
                data_key = first_item.data(Qt.ItemDataRole.UserRole)
                if data_key is not None:
                    default_key = str(data_key)

        if default_key:
            self.select_section_by_key(default_key)

    def _populate_sections(self) -> None:
        for key, title, body in _build_sections():
            self._append_section(key, title, body)

    def _append_section(self, key: str, title: str, body: str) -> None:
        display_title = _clean_section_title(title)
        item = QListWidgetItem(display_title)
        item.setData(Qt.ItemDataRole.UserRole, key)
        item.setToolTip(display_title)
        self._category_list.addItem(item)

        section_widget = _create_section_widget(title, body)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setWidget(section_widget)
        scroll.viewport().installEventFilter(self._content_click_filter)
        section_widget.installEventFilter(self._content_click_filter)
        self._stack.addWidget(scroll)

        index = self._stack.count() - 1
        self._key_to_index[key] = index

    def _toggle_menu(self, checked: bool) -> None:
        """Exibe ou oculta o painel de categorias ajustando largura fixa."""
        self._categoria_container.setVisible(checked)
        self._categoria_container.setFixedWidth(200 if checked else 0)
        self._menu_button.setText("✖ Fechar categorias" if checked else "☰ Categorias")

    def _on_category_changed(self, row: int) -> None:
        if row < 0 or row >= self._stack.count():
            return
        if self._stack.currentIndex() != row:
            self._stack.setCurrentIndex(row)

    # Seleção já reflete estado; chave pode ser obtida por current_key.

    def collapse_menu_on_content_click(self) -> None:
        """Recolhe o menu lateral independentemente do estado (idempotente)."""
        self._menu_button.setChecked(False)

    def position_near_parent(self, gap: int = 10) -> None:
        """Posiciona a janela próxima à janela pai (se existir).

        Estratégia:
        1. Tenta posicionar à direita do parent com um espaçamento (gap).
        2. Se não couber, tenta à esquerda.
        3. Se nenhum dos lados couber integralmente, ajusta dentro da área disponível da tela.
        4. Se não houver parent visível, centraliza na tela primária.

        Parametros
        ----------
        gap: int
            Espaço em pixels entre a borda do parent e esta janela.
        """
        anchor = self.parentWidget()
        if anchor is None or not anchor.isVisible():
            screen = QApplication.primaryScreen()
            if screen:
                geo = screen.availableGeometry()
                self.move(
                    geo.center().x() - self.width() // 2,
                    geo.center().y() - self.height() // 2,
                )
            return

        size = self.size()
        if size.width() <= 0 or size.height() <= 0:
            size = self.sizeHint()

        screen = anchor.screen() or QApplication.primaryScreen()
        if screen is None:
            return
        available = screen.availableGeometry()
        anchor_geo = anchor.frameGeometry()

        width = size.width()
        height = size.height()

        right_option = anchor_geo.right() + gap
        left_option = anchor_geo.left() - gap - width

        if right_option + width <= available.right():
            x = right_option
        elif left_option >= available.left():
            x = left_option
        else:
            x = max(available.left(), min(right_option, available.right() - width))

        y = max(available.top(), min(anchor_geo.top(), available.bottom() - height))
        self.move(int(x), int(y))

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

        current_item = self._category_list.item(index)
        if current_item:
            self._category_list.scrollToItem(
                current_item, QListWidget.ScrollHint.PositionAtCenter
            )

    @property
    def current_key(self) -> Optional[str]:
        """Chave da seção atualmente selecionada (ou None)."""
        item = self._category_list.currentItem()
        if not item:
            return None
        data_key = item.data(Qt.ItemDataRole.UserRole)
        return str(data_key) if data_key is not None else None


def _clear_manual_instance() -> None:
    """Limpa a instância ativa registrada do manual."""

    global _manual_instance  # pylint: disable=global-statement
    _manual_instance = None


def show_manual(
    root: Optional[QWidget],
    initial_key: Optional[str] = None,
) -> ManualDialog:
    """Exibe o manual, reutilizando a janela existente se já estiver aberta."""

    global _manual_instance  # pylint: disable=global-statement
    # Se root não for fornecido (ex.: chamado a partir do menu), tentar localizar a
    # janela principal do aplicativo para usar como âncora de posicionamento.
    if root is None:
        # Preferir a janela ativa do QApplication
        root = QApplication.activeWindow()
        if root is None:
            # Fallback: procurar o primeiro top-level widget visível que não seja
            # o próprio diálogo do manual (caso já exista)
            for w in QApplication.topLevelWidgets():
                # Evitar usar a instância do manual como âncora
                if w is _manual_instance:
                    continue
                if isinstance(w, QWidget) and w.isVisible():
                    root = w
                    break

    if _manual_instance is None or not _manual_instance.isVisible():
        if _manual_instance is not None:
            try:
                _manual_instance.deleteLater()
            except RuntimeError:
                pass
        _manual_instance = ManualDialog(root, initial_key)
        _manual_instance.destroyed.connect(_clear_manual_instance)
        # Posiciona o diálogo próximo ao parent (se houver) ou centraliza
        _manual_instance.position_near_parent()
        _manual_instance.show()
    else:
        if initial_key:
            _manual_instance.select_section_by_key(initial_key)

    if initial_key:
        _manual_instance.select_section_by_key(initial_key)

    _manual_instance.raise_()
    _manual_instance.activateWindow()

    return _manual_instance


context_help.register_manual_launcher(
    lambda parent, key, _block: show_manual(parent, key)
)


def main(root: Optional[QWidget]) -> ManualDialog:
    """Compatibilidade com chamadas existentes que abrem o manual."""

    return show_manual(root)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    _dialog = main(None)
    sys.exit(app.exec())
