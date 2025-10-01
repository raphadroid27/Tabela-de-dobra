"""Widgets de tabela compartilhados entre formulários."""

from __future__ import annotations

import os
from typing import Iterable, List, Mapping, Sequence, Set

from PySide6.QtCore import Qt
from PySide6.QtGui import QDropEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)

from src.utils.estilo import aplicar_estilo_table_widget
from src.utils.utilitarios import (
    FILE_OPEN_EXCEPTIONS,
    open_file_with_default_app,
    show_error,
    show_warning,
)


class FileDropTableWidget(QTableWidget):
    """Tabela base que aceita arrastar e soltar arquivos."""

    # pylint: disable=invalid-name

    missing_file_title = "Arquivo Não Encontrado"
    error_opening_title = "Erro ao Abrir Arquivo"

    def __init__(self, parent=None, path_column: int = 1) -> None:
        """Inicializa a tabela base com coluna de caminho e sinal padrão."""
        super().__init__(parent)
        self._path_column = path_column
        self._allowed_extensions: tuple[str, ...] = ()
        self.itemDoubleClicked.connect(self._on_item_double_clicked)

    # ------------------------------------------------------------------
    # Configuração de extensões permitidas
    # ------------------------------------------------------------------
    def set_allowed_extensions(self, extensions: Sequence[str]) -> None:
        """Define as extensões aceitas para arrastar/soltar."""
        cleaned: List[str] = []
        for ext in extensions:
            if not ext:
                continue
            ext = ext.replace("*", "").strip().lower()
            if ext and not ext.startswith("."):
                ext = f".{ext}"
            if ext:
                cleaned.append(ext)
        self._allowed_extensions = tuple(cleaned)

    # ------------------------------------------------------------------
    # Eventos de arrastar/soltar
    # ------------------------------------------------------------------
    def dragEnterEvent(self, event: QDropEvent) -> None:
        """Aceita o arraste quando houver arquivos com extensão válida."""
        if self._should_accept(event):
            event.acceptProposedAction()

    def dragMoveEvent(self, event: QDropEvent) -> None:
        """Mantém o evento aceito enquanto o cursor se move sobre a tabela."""
        event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        """Processa os arquivos soltos sobre a tabela."""
        files = [
            path
            for path in self._iter_local_paths(event)
            if self._is_extension_allowed(path)
        ]
        if files:
            self.handle_dropped_files(files)

    # ------------------------------------------------------------------
    # Interface para subclasses
    # ------------------------------------------------------------------
    def handle_dropped_files(self, files: Iterable[str]) -> None:
        """Processa os arquivos arrastados adicionando-os à tabela."""
        self.add_files(list(files))

    def add_files(self, file_paths: Sequence[str]) -> None:
        """Adiciona arquivos, evitando duplicidades."""
        existing = self._collect_existing_paths().union(self._collect_external_paths())
        added: List[str] = []
        for path in file_paths:
            if path in existing:
                continue
            self._insert_path(path)
            existing.add(path)
            added.append(path)

        if added:
            self.on_files_added(added)
        duplicates = len(file_paths) - len(added)
        if duplicates:
            self.on_duplicates_skipped(duplicates)

    def _insert_path(self, path: str) -> None:
        """Insere na tabela uma linha correspondente ao caminho informado."""
        raise NotImplementedError

    def on_files_added(self, added_paths: Sequence[str]) -> None:  # pragma: no cover
        """Trata os arquivos recém-adicionados (gancho de extensão)."""

    def on_duplicates_skipped(self, count: int) -> None:  # pragma: no cover
        """Emit a warning when duplicated files are skipped."""
        if count:
            show_warning(
                "Arquivos Ignorados",
                f"{count} arquivo(s) ignorado(s) por já existirem na lista.",
                parent=self.window(),
            )

    def on_missing_file(self, file_path: str | None) -> None:  # pragma: no cover
        """Informa ao utilizador quando o arquivo não está acessível."""
        if not file_path:
            return
        show_warning(
            self.missing_file_title,
            f"O arquivo '{os.path.basename(file_path)}' não foi encontrado.",
            parent=self.window(),
        )

    def on_open_error(self, error: Exception) -> None:  # pragma: no cover
        """Informa ao utilizador quando ocorre erro ao abrir o arquivo."""
        show_error(
            self.error_opening_title,
            f"Não foi possível abrir o arquivo:\n{error}",
            parent=self.window(),
        )

    # ------------------------------------------------------------------
    # Utilidades internas
    # ------------------------------------------------------------------
    def _iter_local_paths(self, event: QDropEvent) -> Iterable[str]:
        for url in event.mimeData().urls():
            if url.isLocalFile():
                yield url.toLocalFile()

    def _collect_existing_paths(self) -> Set[str]:
        existing: Set[str] = set()
        for row in range(self.rowCount()):
            item = self.item(row, self._path_column)
            if not item:
                continue
            data = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(data, str):
                existing.add(data)
        return existing

    def _collect_external_paths(self) -> Set[str]:
        """Permite que subclasses incluam caminhos externos para verificação."""
        return set()

    def _should_accept(self, event: QDropEvent) -> bool:
        if not event.mimeData().hasUrls():
            return False
        return any(
            self._is_extension_allowed(path) for path in self._iter_local_paths(event)
        )

    def _is_extension_allowed(self, file_path: str) -> bool:
        if not self._allowed_extensions:
            return True
        return file_path.lower().endswith(self._allowed_extensions)

    def _on_item_double_clicked(self, item: QTableWidgetItem) -> None:
        if item.column() != self._path_column:
            return
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(file_path, str) or not os.path.exists(file_path):
            self.on_missing_file(file_path if isinstance(file_path, str) else None)
            return
        try:
            open_file_with_default_app(file_path)
        except FILE_OPEN_EXCEPTIONS as exc:  # pragma: no cover
            self.on_open_error(exc)


class StyledFileTableWidget(FileDropTableWidget):
    """Tabela com configurações padrão para formulários de arquivos."""

    def __init__(self, parent=None, path_column: int = 1) -> None:
        """Inicializa a tabela estilizada com comportamentos padrão."""
        super().__init__(parent, path_column)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        aplicar_estilo_table_widget(self)
        self.verticalHeader().setVisible(False)

    def configure_columns(
        self,
        headers: Sequence[str],
        *,
        fixed_widths: Mapping[int, int] | None = None,
        stretch_columns: Sequence[int] | None = None,
    ) -> None:
        """Configura cabeçalhos e larguras das colunas."""
        header_view = self.horizontalHeader()
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(list(headers))

        for index in range(len(headers)):
            header_view.setSectionResizeMode(index, QHeaderView.ResizeMode.Stretch)

        if fixed_widths:
            for index, width in fixed_widths.items():
                header_view.setSectionResizeMode(index, QHeaderView.ResizeMode.Fixed)
                self.setColumnWidth(index, width)

        if stretch_columns:
            for index in stretch_columns:
                header_view.setSectionResizeMode(index, QHeaderView.ResizeMode.Stretch)

    def _insert_path(self, path: str) -> None:  # pragma: no cover
        """Permite que subclasses definam a inserção específica de linhas."""
        raise NotImplementedError
