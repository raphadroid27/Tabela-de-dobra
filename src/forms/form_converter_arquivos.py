"""
Formulário de Conversão de Arquivos.

Este módulo implementa um formulário para conversão de arquivos, com um layout
inspirado no formulário de comparação para manter a consistência da UI.
Utiliza uma thread para processamento em segundo plano, garantindo que a interface
permaneça responsiva durante a conversão.

A versão otimizada adiciona a funcionalidade de cancelamento, tratamento de
exceções globais na thread e deteção automática de softwares externos.
"""

# pylint: disable= R1702,R0902,R0911,R0913,R0914,R0915,R0917,C0103

import logging
import os
import sys
from typing import List, Optional, Sequence

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.forms.common import context_help
from src.forms.common.file_tables import ManagedFileTableWidget
from src.forms.common.form_manager import BaseSingletonFormManager
from src.forms.common.ui_helpers import (
    attach_actions_with_progress,
    create_dialog_scaffold,
    request_worker_cancel,
    stop_worker_on_error,
    update_processing_state,
)
from src.forms.converter_worker import CONVERSION_HANDLERS, ConversionWorker
from src.utils.estilo import (
    aplicar_estilo_botao,
    aplicar_estilo_table_widget,
)
from src.utils.utilitarios import (
    FILE_OPEN_EXCEPTIONS,
    ICON_PATH,
    aplicar_medida_borda_espaco,
    open_file_with_default_app,
    show_error,
    show_info,
    show_warning,
)

# --- Configuração da UI ---
LARGURA_FORM_CONVERSAO = 500
ALTURA_FORM_CONVERSAO = 500
MARGEM_LAYOUT_PRINCIPAL = 10


class FileTableWidget(ManagedFileTableWidget):
    """Tabela personalizada para exibir arquivos."""

    files_added = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent, path_column=1)
        self.configure_columns(
            ["#", "Arquivo"], fixed_widths={0: 30}, stretch_columns=(1,)
        )

    # type: ignore[override]
    def set_allowed_extensions(self, extensions: List[str]) -> None:
        super().set_allowed_extensions(extensions)

    def _insert_path(self, path: str) -> None:
        row = self.rowCount()
        self.insertRow(row)
        self.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        file_item = QTableWidgetItem(os.path.basename(path))
        file_item.setData(Qt.ItemDataRole.UserRole, path)
        file_item.setToolTip(path)
        self.setItem(row, 1, file_item)

    def on_files_added(self, added_paths: List[str]) -> None:  # type: ignore[override]
        self.files_added.emit(added_paths)


class FormConverterArquivos(QDialog):
    """Formulário para Conversão de Arquivos."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker: Optional[ConversionWorker] = None
        self.cmb_conversion_type: Optional[QComboBox] = None
        self.tabela_origem: Optional[FileTableWidget] = None
        self.tabela_resultado: Optional[QTableWidget] = None
        self.destino_entry: Optional[QLineEdit] = None
        self.btn_converter: Optional[QPushButton] = None
        self.btn_cancel: Optional[QPushButton] = None
        self.btn_limpar: Optional[QPushButton] = None
        self.progress_bar: Optional[QProgressBar] = None
        self._inicializar_ui()

    def _inicializar_ui(self):
        """Configura a interface gráfica do formulário."""
        vlayout = create_dialog_scaffold(
            self,
            title="Conversor de Arquivos",
            size=(LARGURA_FORM_CONVERSAO, ALTURA_FORM_CONVERSAO),
            icon_path=ICON_PATH,
            position="direita",
            barra_title="Conversor de Arquivos",
            help_callback=self._mostrar_ajuda,
            help_tooltip="Guia de uso do conversor",
        )

        conteudo = QWidget()
        layout_principal = QVBoxLayout(conteudo)
        aplicar_medida_borda_espaco(layout_principal, MARGEM_LAYOUT_PRINCIPAL)
        vlayout.addWidget(conteudo)

        self._setup_layouts(layout_principal)
        self._on_conversion_type_changed()

    def _mostrar_ajuda(self) -> None:
        """Mostra as instruções rápidas desta janela."""
        context_help.show_help("converter", parent=self)

    def _setup_layouts(self, main_layout: QVBoxLayout):
        """Cria e organiza os widgets da UI."""
        # Linha de seleção de tipo
        type_layout = QHBoxLayout()
        label_tipo = QLabel("Tipo de Conversão:")
        label_tipo.setObjectName("label_titulo")
        type_layout.addWidget(label_tipo)
        self.cmb_conversion_type = QComboBox()
        self.cmb_conversion_type.addItems(CONVERSION_HANDLERS.keys())
        self.cmb_conversion_type.setToolTip(
            "Selecione o tipo de conversão que deseja executar."
        )
        self.cmb_conversion_type.currentTextChanged.connect(
            self._on_conversion_type_changed
        )
        type_layout.addWidget(self.cmb_conversion_type, 1)
        main_layout.addLayout(type_layout)

        # Área principal de tabelas
        tables_layout = QHBoxLayout()
        self.tabela_origem = FileTableWidget()
        self.tabela_origem.files_added.connect(self._on_files_added)
        self.tabela_origem.setToolTip(
            "Arquivos de entrada para converter. Arraste, solte ou use o botão ao lado."
        )
        self.tabela_resultado = self._criar_tabela_resultado()
        self.tabela_resultado.setToolTip(
            "Resultados gerados. Dê um duplo clique para abrir o arquivo de saída."
        )

        # Botão de adicionar arquivos (atalho Ctrl+O)
        btn_add = QPushButton("➕ Adicionar Arquivos")
        btn_add.setToolTip("Selecionar arquivos de origem (Ctrl+O)")
        btn_add.setShortcut("Ctrl+O")
        btn_add.clicked.connect(self._select_files)
        aplicar_estilo_botao(btn_add, "cinza")

        destino_widget = self._criar_widget_destino()

        tables_layout.addWidget(
            self._criar_groupbox("Arquivos de Origem", self.tabela_origem, btn_add)
        )
        tables_layout.addWidget(
            self._criar_groupbox("Resultado", self.tabela_resultado, destino_widget)
        )
        main_layout.addLayout(tables_layout, 1)

        # Barra de ações inferiores
        action_layout = QHBoxLayout()
        self.btn_converter = QPushButton("🚀 Converter")
        self.btn_converter.setToolTip(
            "Iniciar a conversão usando o tipo selecionado (Ctrl+Enter)"
        )
        self.btn_converter.setShortcut("Ctrl+Return")
        self.btn_converter.clicked.connect(self.executar_conversao)
        aplicar_estilo_botao(self.btn_converter, "verde")

        self.btn_cancel = QPushButton("🛑 Cancelar")
        self.btn_cancel.setToolTip("Cancelar o processamento atual (Esc)")
        self.btn_cancel.setShortcut("Esc")
        self.btn_cancel.clicked.connect(self._cancel_conversion)
        self.btn_cancel.setEnabled(False)
        aplicar_estilo_botao(self.btn_cancel, "laranja")

        self.btn_limpar = QPushButton("🧹 Limpar")
        self.btn_limpar.setToolTip(
            "Limpar listas de arquivos e reiniciar o formulário (Ctrl+L)"
        )
        self.btn_limpar.setShortcut("Ctrl+L")
        self.btn_limpar.clicked.connect(self._clear_all)
        aplicar_estilo_botao(self.btn_limpar, "vermelho")

        action_layout.addWidget(self.btn_converter)
        action_layout.addWidget(self.btn_limpar)
        action_layout.addWidget(self.btn_cancel)

        self.progress_bar = attach_actions_with_progress(main_layout, action_layout)
        self.progress_bar.setToolTip("Progresso da conversão em andamento.")

    def _criar_tabela_resultado(self) -> QTableWidget:
        """Cria e configura a tabela de resultados."""
        table = QTableWidget()
        aplicar_estilo_table_widget(table)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.itemDoubleClicked.connect(self._abrir_arquivo_resultado)
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["#", "Arquivo", "Status"])
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.setColumnWidth(0, 30)
        table.setColumnWidth(2, 45)
        table.verticalHeader().setVisible(False)
        return table

    def _criar_widget_destino(self) -> QWidget:
        """Cria o widget para seleção da pasta de destino."""
        self.destino_entry = QLineEdit()
        self.destino_entry.setPlaceholderText("Pasta de Destino...")
        self.destino_entry.setToolTip(
            "Informe a pasta onde os arquivos convertidos serão salvos."
        )
        btn_destino = QPushButton("📁 Procurar")
        btn_destino.setToolTip("Selecionar uma pasta de destino pelo explorador.")
        btn_destino.clicked.connect(self._selecionar_pasta_destino)
        aplicar_estilo_botao(btn_destino, "cinza")
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.destino_entry)
        layout.addWidget(btn_destino)
        return widget

    def _criar_groupbox(self, title, table, top_widget):
        """Cria um QGroupBox para agrupar widgets."""
        gb = QGroupBox(title)
        layout = QVBoxLayout(gb)
        if top_widget:
            layout.addWidget(top_widget)
        layout.addWidget(table)
        aplicar_medida_borda_espaco(layout, 5)
        return gb

    def _on_files_added(self, added_paths: List[str]):
        """Define a pasta de destino com base no primeiro arquivo adicionado."""
        if not self.destino_entry.text() and added_paths:
            self.destino_entry.setText(os.path.dirname(added_paths[0]))

    def _abrir_arquivo_resultado(self, item: QTableWidgetItem):
        """Abre o arquivo correspondente ao item da tabela de resultados."""
        if item.column() != 1:
            return
        path = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(path, str) or not os.path.exists(path):
            filename = os.path.basename(path) if isinstance(path, str) else ""
            show_warning(
                "Arquivo Não Encontrado",
                f"O arquivo '{filename}' não foi encontrado.",
                parent=self,
            )
            return
        try:
            open_file_with_default_app(path)
        except FILE_OPEN_EXCEPTIONS as exc:  # pragma: no cover
            show_error(
                "Erro ao Abrir", f"Não foi possível abrir o arquivo:\n{exc}", self
            )

    def _on_conversion_type_changed(self):
        """Atualiza a UI quando o tipo de conversão é alterado."""
        self._clear_all()
        conv_type = self.cmb_conversion_type.currentText()
        if handler := CONVERSION_HANDLERS.get(conv_type):
            self.tabela_origem.set_allowed_extensions(handler["extensions"])
            self.btn_converter.setToolTip(handler["tooltip"])
            self.btn_converter.setEnabled(handler["enabled"])
            if not handler["enabled"]:
                show_warning("Dependência em Falta", handler["dependency_msg"], self)

    def _selecionar_pasta_destino(self):
        """Abre um diálogo para selecionar a pasta de destino."""
        if directory := QFileDialog.getExistingDirectory(
            self, "Selecionar Pasta de Destino"
        ):
            self.destino_entry.setText(directory)

    def _select_files(self):
        """Abre o diálogo para selecionar arquivos de origem."""
        if not (
            handler := CONVERSION_HANDLERS.get(self.cmb_conversion_type.currentText())
        ):
            return
        extensions = " ".join(handler["extensions"])
        dialog_filter = f"Arquivos ({extensions});;Todos os arquivos (*)"
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Selecionar Arquivos", "", dialog_filter
        )
        if file_paths:
            self.tabela_origem.add_files(file_paths)

    def _clear_all(self):
        """Limpa as tabelas e campos de entrada."""
        if self.worker:
            return
        self.tabela_origem.setRowCount(0)
        self.tabela_resultado.setRowCount(0)
        self.destino_entry.clear()
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)

    def executar_conversao(self):
        """Inicia o processo de conversão dos arquivos."""
        if not self.destino_entry.text() or not os.path.isdir(
            self.destino_entry.text()
        ):
            show_error(
                "Erro", "A pasta de destino deve ser selecionada e válida.", self
            )
            return
        if self.tabela_origem.rowCount() == 0:
            show_warning("Aviso", "Não há arquivos para converter.", self)
            return

        self._set_ui_state(is_running=True)
        files = [
            (r, self.tabela_origem.item(r, 1).data(Qt.ItemDataRole.UserRole))
            for r in range(self.tabela_origem.rowCount())
        ]
        self.tabela_resultado.setRowCount(len(files))
        for row, (_, path) in enumerate(files):
            self.tabela_resultado.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            self.tabela_resultado.setItem(
                row, 1, QTableWidgetItem(os.path.basename(path))
            )
            self.tabela_resultado.setItem(row, 2, QTableWidgetItem("..."))

        conv_type = self.cmb_conversion_type.currentText()
        self.worker = ConversionWorker(self.destino_entry.text(), files, conv_type)
        self.worker.progress_percent.connect(self.progress_bar.setValue)
        self.worker.file_processed.connect(self._update_file_status)
        self.worker.processo_finalizado.connect(self._on_conversion_finished)
        self.worker.error_occurred.connect(self._on_worker_error)
        self.worker.start()

    def _cancel_conversion(self):
        """Solicita o cancelamento da thread de conversão."""
        request_worker_cancel(self.worker, self.btn_cancel)

    def _on_worker_error(self, message: str):
        """Chamado quando um erro não tratado ocorre na thread."""
        stop_worker_on_error(self.worker, self.btn_cancel)
        show_error("Erro Inesperado na Conversão", message, self)

    def _set_ui_state(self, is_running: bool):
        """Habilita/desabilita os controlos da UI com base no estado da operação."""
        update_processing_state(
            is_running,
            [self.btn_converter, self.btn_limpar, self.cmb_conversion_type],
            self.btn_cancel,
            self.progress_bar,
        )

    def _update_file_status(self, row, new_path, success, message):
        """Atualiza o status de um arquivo na tabela de resultados."""
        color = QColor("#4CAF50") if success else QColor("#F44336")
        status_item = QTableWidgetItem("✓" if success else "✗")
        status_item.setForeground(color)
        status_item.setToolTip(message)
        self.tabela_resultado.setItem(row, 2, status_item)
        if success:
            file_item = self.tabela_resultado.item(row, 1)
            paths: List[str] = []
            if isinstance(new_path, str):
                paths = [new_path]
            elif isinstance(new_path, Sequence):
                for candidate in new_path:
                    if isinstance(candidate, os.PathLike):
                        paths.append(os.fspath(candidate))
                    elif isinstance(candidate, str):
                        paths.append(candidate)

            if not paths:
                paths = [""]

            principal = paths[0]
            extra_count = max(0, len(paths) - 1)
            display_name = os.path.basename(principal) if principal else "—"
            if extra_count:
                display_name = f"{display_name} (+{extra_count})"

            tooltip_lines = [path for path in paths if path]
            if message:
                tooltip_lines.append(message)

            file_item.setText(display_name)
            file_item.setToolTip("\n".join(tooltip_lines))
            file_item.setData(Qt.ItemDataRole.UserRole, principal)

    def _on_conversion_finished(self, was_cancelled: bool):
        """Executado quando a thread de conversão termina."""
        self._set_ui_state(is_running=False)
        self.worker = None
        if was_cancelled and self.btn_cancel.text() == "Aguarde...":
            msg = "Conversão cancelada."
        else:
            msg = "Conversão de arquivos finalizada."

        if not was_cancelled:
            show_info("Informação", msg, self)

        QTimer.singleShot(2000, lambda: self.progress_bar.setVisible(False))


class FormManager(BaseSingletonFormManager):
    """Gerencia a instância do formulário para evitar múltiplas janelas."""

    FORM_CLASS = FormConverterArquivos


def main(parent=None):
    """Ponto de entrada para exibir o formulário."""
    FormManager.show_form(parent)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Configuração básica do logging para ver as saídas na consola
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    )
    main()
    sys.exit(app.exec())
