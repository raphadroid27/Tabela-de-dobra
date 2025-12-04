"""
Módulo para o formulário de Comparador Geométrico de Arquivos.

Este formulário permite aos utilizadores carregar arquivos (STEP, IGES, PDF, DXF, DWG)
em duas listas lado a lado e realizar uma comparação detalhada.
A comparação utiliza bibliotecas específicas para cada tipo de arquivo para
extrair e comparar propriedades relevantes.

A versão otimizada move a lógica de comparação para uma thread em segundo
plano para manter a interface responsiva.
"""

# pylint: disable=R0902,R0911,R0913,R0914,R0915,R0917,C0103

import logging
import os
import sys
from typing import Optional, Set

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
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
from src.utils.comparar_worker import (
    FILE_HANDLERS,
    ComparisonWorker,
    get_missing_dependencies,
)
from src.utils.estilo import aplicar_estilo_botao
from src.utils.utilitarios import (
    ICON_PATH,
    aplicar_medida_borda_espaco,
    show_error,
    show_info,
    show_warning,
)

# --- Constantes de Configuração ---
LARGURA_FORM = 500
ALTURA_FORM = 510
MARGEM_LAYOUT = 10


class FileTableWidget(ManagedFileTableWidget):
    """Tabela que aceita arquivos arrastados e permite reordenação e exclusão."""

    def __init__(self, parent=None):
        """Inicializa a tabela configurando colunas e estado inicial."""
        super().__init__(parent, path_column=1)
        self.configure_columns(
            ["#", "Arquivo", "Status"],
            fixed_widths={0: 30, 2: 45},
            stretch_columns=(1,),
        )

        self.other_table: Optional["FileTableWidget"] = None

    def set_other_table(self, other_table: "FileTableWidget") -> None:
        """Define uma referência à outra tabela para verificação de duplicados."""
        self.other_table = other_table

    def _collect_external_paths(self) -> Set[str]:
        if not self.other_table:
            return set()
        paths: Set[str] = set()
        for row in range(self.other_table.rowCount()):
            item = self.other_table.item(row, 1)
            if item:
                data = item.data(Qt.ItemDataRole.UserRole)
                if isinstance(data, str):
                    paths.add(data)
        return paths

    def _insert_path(self, path: str) -> None:
        row = self.rowCount()
        self.insertRow(row)
        num_item = QTableWidgetItem(str(row + 1))
        num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        file_item = QTableWidgetItem(os.path.basename(path))
        file_item.setData(Qt.ItemDataRole.UserRole, path)
        file_item.setToolTip(path)
        status_item = QTableWidgetItem("")
        status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setItem(row, 0, num_item)
        self.setItem(row, 1, file_item)
        self.setItem(row, 2, status_item)

    def on_duplicates_skipped(self, count: int) -> None:
        """Apresenta um aviso quando arquivos duplicados são ignorados."""
        logging.warning("%d arquivo(s) ignorado(s) por duplicidade.", count)
        show_warning(
            "Arquivos Ignorados",
            f"{count} arquivo(s) ignorado(s) por já existirem na lista.",
            parent=self.window(),
        )

    def on_missing_file(self, file_path: str | None) -> None:
        """Registra e delega o tratamento quando um arquivo está ausente."""
        if file_path:
            logging.warning("Tentativa de abrir arquivo inexistente: %s", file_path)
        super().on_missing_file(file_path)


class FormCompararArquivos(QDialog):
    """Formulário para Comparação de Arquivos."""

    def __init__(self, parent=None):
        """Configura o formulário e inicializa widgets principais."""
        super().__init__(parent)
        self.worker: Optional[ComparisonWorker] = None
        self.table_a_widget: Optional[FileTableWidget] = None
        self.table_b_widget: Optional[FileTableWidget] = None
        self.progress_bar: Optional[QProgressBar] = None
        self.btn_compare: Optional[QPushButton] = None
        self.btn_cancel: Optional[QPushButton] = None
        self.btn_clear: Optional[QPushButton] = None
        self.cmb_file_type: Optional[QComboBox] = None
        self._inicializar_ui()

    def _inicializar_ui(self):
        """Inicializa a interface do utilizador."""
        vlayout = create_dialog_scaffold(
            self,
            title="Comparador de Arquivos",
            size=(LARGURA_FORM, ALTURA_FORM),
            icon_path=ICON_PATH,
            barra_title="Comparador de Arquivos",
            position="direita",
            help_callback=self._mostrar_ajuda,
            help_tooltip="Guia de uso do comparador",
        )

        conteudo = QWidget()
        layout_principal = QVBoxLayout(conteudo)
        aplicar_medida_borda_espaco(layout_principal, MARGEM_LAYOUT)
        vlayout.addWidget(conteudo)

        self._check_dependencies()
        self._setup_layouts(layout_principal)
        self._on_file_type_changed()

    def _mostrar_ajuda(self) -> None:
        """Mostra as instruções rápidas desta janela."""
        context_help.show_help("comparar", parent=self)

    def _check_dependencies(self):
        """Verifica as dependências e informa o utilizador sobre as que faltam."""
        missing = get_missing_dependencies()
        if missing:
            msg = "Bibliotecas opcionais não encontradas:\n\n- " + "\n- ".join(missing)
            msg += "\n\nFuncionalidades relacionadas estarão desativadas."
            logging.warning("Dependências opcionais ausentes: %s", ", ".join(missing))
            show_info("Dependências Opcionais", msg, parent=self)

    def _setup_layouts(self, main_layout: QVBoxLayout):
        """Configura os layouts internos do formulário."""
        type_layout = QHBoxLayout()
        label_tipo = QLabel("Tipo de Arquivo:")
        label_tipo.setObjectName("label_titulo")
        type_layout.addWidget(label_tipo)
        self.cmb_file_type = QComboBox()
        for name, data in FILE_HANDLERS.items():
            if data["available"]:
                self.cmb_file_type.addItem(name)
        self.cmb_file_type.setToolTip("Selecione o tipo de arquivo para comparar.")
        self.cmb_file_type.currentTextChanged.connect(self._on_file_type_changed)
        type_layout.addWidget(self.cmb_file_type, 1)
        main_layout.addLayout(type_layout)

        lists_layout = QHBoxLayout()
        self.table_a_widget = FileTableWidget()
        self.table_b_widget = FileTableWidget()
        self.table_a_widget.set_other_table(self.table_b_widget)
        self.table_b_widget.set_other_table(self.table_a_widget)
        self.table_a_widget.setToolTip(
            "Arraste arquivos ou use o botão acima para adicioná-los à Lista A."
        )
        self.table_b_widget.setToolTip(
            "Arraste arquivos ou use o botão acima para adicioná-los à Lista B."
        )
        lists_layout.addWidget(
            self._create_list_groupbox("Lista A", self.table_a_widget, "Ctrl+1")
        )
        lists_layout.addWidget(
            self._create_list_groupbox("Lista B", self.table_b_widget, "Ctrl+2")
        )
        main_layout.addLayout(lists_layout)

        action_layout = QHBoxLayout()
        self.btn_compare = QPushButton("🔄 Comparar")
        self.btn_compare.setToolTip(
            "Comparar arquivos presentes nas duas listas (Ctrl+Enter)"
        )
        self.btn_compare.setShortcut("Ctrl+Return")
        self.btn_compare.clicked.connect(self.iniciar_comparacao)
        aplicar_estilo_botao(self.btn_compare, "verde")
        self.btn_cancel = QPushButton("🛑 Cancelar")
        self.btn_cancel.setToolTip("Cancelar a comparação em andamento (Esc)")
        self.btn_cancel.setShortcut("Esc")
        self.btn_cancel.clicked.connect(self._cancel_comparison)
        self.btn_cancel.setEnabled(False)
        aplicar_estilo_botao(self.btn_cancel, "laranja")
        self.btn_clear = QPushButton("🧹 Limpar")
        self.btn_clear.setToolTip("Remover todos os itens das listas A e B (Ctrl+L)")
        self.btn_clear.setShortcut("Ctrl+L")
        self.btn_clear.clicked.connect(self._clear_all)
        aplicar_estilo_botao(self.btn_clear, "vermelho")
        action_layout.addWidget(self.btn_compare)
        action_layout.addWidget(self.btn_clear)
        action_layout.addWidget(self.btn_cancel)
        self.progress_bar = attach_actions_with_progress(main_layout, action_layout)

    def _create_list_groupbox(
        self, title: str, table: FileTableWidget, shortcut: str
    ) -> QGroupBox:
        """Cria um QGroupBox contendo uma tabela e um botão de adicionar."""
        groupbox = QGroupBox(title)
        layout = QVBoxLayout(groupbox)
        btn_add = QPushButton(f"➕ Adicionar à {title}")
        btn_add.setToolTip(f"Selecionar arquivos e adicioná-los à {title} ({shortcut})")
        btn_add.setShortcut(shortcut)
        btn_add.clicked.connect(lambda: self._select_files(table))
        aplicar_estilo_botao(btn_add, "cinza")
        layout.addWidget(btn_add)
        layout.addWidget(table)
        aplicar_medida_borda_espaco(layout, 5)
        return groupbox

    def _on_file_type_changed(self):
        """Chamado quando o tipo de arquivo no ComboBox muda."""
        self._clear_all()
        file_type = self.cmb_file_type.currentText()
        if handler := FILE_HANDLERS.get(file_type):
            extensions = handler["extensions"]
            self.table_a_widget.set_allowed_extensions(extensions)
            self.table_b_widget.set_allowed_extensions(extensions)
            self.btn_compare.setToolTip(handler["tooltip"])

    def _select_files(self, table: FileTableWidget):
        """Abre uma caixa de diálogo para selecionar arquivos."""
        file_type = self.cmb_file_type.currentText()
        if not (handler := FILE_HANDLERS.get(file_type)):
            return

        extensions = " ".join(handler["extensions"])
        dialog_filter = f"Arquivos {file_type} ({extensions});;Todos os Arquivos (*)"
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Selecionar Arquivos", "", dialog_filter
        )
        if file_paths:
            table.add_files(file_paths)

    def iniciar_comparacao(self):
        """Prepara e inicia a thread de comparação."""
        if self.table_a_widget.rowCount() == 0 or self.table_b_widget.rowCount() == 0:
            logging.warning(
                "Tentativa de comparação com uma ou ambas as listas vazias."
            )
            show_warning(
                "Atenção", "Adicione arquivos em ambas as listas para comparar.", self
            )
            return

        self._reset_tables_status()
        self._set_ui_state(is_running=True)

        files_a = [
            self.table_a_widget.item(r, 1).data(Qt.ItemDataRole.UserRole)
            for r in range(self.table_a_widget.rowCount())
        ]
        files_b = [
            self.table_b_widget.item(r, 1).data(Qt.ItemDataRole.UserRole)
            for r in range(self.table_b_widget.rowCount())
        ]

        self.worker = ComparisonWorker(
            files_a, files_b, self.cmb_file_type.currentText()
        )
        self.worker.progress_updated.connect(self.progress_bar.setValue)
        self.worker.row_compared.connect(self._on_row_compared)
        self.worker.comparison_finished.connect(self._on_comparison_finished)
        self.worker.error_occurred.connect(self._on_worker_error)
        self.worker.start()

    def _cancel_comparison(self):
        """Solicita o cancelamento da thread de comparação."""
        request_worker_cancel(self.worker, self.btn_cancel)

    def _on_worker_error(self, message: str):
        """Chamado quando um erro não tratado ocorre na thread."""
        stop_worker_on_error(self.worker, self.btn_cancel)
        show_error("Erro Inesperado na Comparação", message, self)

    def _set_ui_state(self, is_running: bool):
        """Habilita/desabilita controles da UI com base no estado da operação."""
        update_processing_state(
            is_running,
            [self.btn_compare, self.btn_clear, self.cmb_file_type],
            self.btn_cancel,
            self.progress_bar,
        )

    def _reset_tables_status(self):
        """Limpa o status e a cor de todas as linhas em ambas as tabelas."""
        for table in (self.table_a_widget, self.table_b_widget):
            for row in range(table.rowCount()):
                status_item = table.item(row, 2)
                if status_item:
                    status_item.setText("")
                for col in range(table.columnCount()):
                    if item := table.item(row, col):
                        item.setForeground(QColor("white"))

    def _on_row_compared(self, row, props_a, status_a, props_b, status_b, are_equal):
        """Atualiza a UI para uma linha que acabou de ser comparada."""
        if row < self.table_a_widget.rowCount():
            self._update_row_status(
                self.table_a_widget, row, props_a, status_a, are_equal
            )
        if row < self.table_b_widget.rowCount():
            self._update_row_status(
                self.table_b_widget, row, props_b, status_b, are_equal
            )

    def _format_properties_tooltip(self, props: Optional[tuple], file_type: str) -> str:
        """Formata as propriedades para exibição na tooltip."""
        if not props:
            return ""
        if props[0] == "Hash idêntico":
            return "\n\nDados idênticos (hash binário)."

        header = "\n\nPropriedades Extraídas:\n"
        lines = []
        if file_type in ("STEP", "IGES"):
            labels = ["Topologia", "Volume", "Área", "Centro de Massa", "Mom. Inércia"]
            lines = [f"  - {lbl}: {val}" for lbl, val in zip(labels, props)]
        elif file_type == "DXF":
            labels = ["Entidades", "Ext. Mínima", "Ext. Máxima"]
            lines = [f"  - {lbl}: {val}" for lbl, val in zip(labels, props)]
        elif file_type == "PDF":
            pages, author, creator, text_hash, image_count, image_hash, file_hash = (
                props
            )
            lines = [
                f"  - Páginas: {pages}",
                f"  - Autor: {author}",
                f"  - Criador: {creator}",
                f"  - Hash Texto: {self._short_hash(text_hash)}",
                f"  - Imagens: {image_count}",
            ]
            if image_count:
                lines.append(f"  - Hash Imagens: {self._short_hash(image_hash)}")
            if file_hash:
                lines.append(f"  - Hash Binário: {self._short_hash(file_hash)}")
        elif file_type == "DWG":
            lines = [f"  - Hash SHA256: {self._short_hash(props[0], 32)}"]
        return header + "\n".join(lines)

    @staticmethod
    def _short_hash(value: str, prefix: int = 24) -> str:
        if not value:
            return "-"
        return value if len(value) <= prefix else f"{value[:prefix]}..."

    def _update_row_status(
        self,
        table: QTableWidget,
        row: int,
        props: tuple,
        status_msg: str,
        are_equal: Optional[bool],
    ):
        """Atualiza a cor e a tooltip de uma linha com base no resultado."""
        status_item = table.item(row, 2)
        file_item = table.item(row, 1)
        if not file_item or not status_item:
            return

        tooltip = f"Caminho: {file_item.data(Qt.ItemDataRole.UserRole)}"
        tooltip += self._format_properties_tooltip(
            props, self.cmb_file_type.currentText()
        )

        if status_msg != "OK":
            status_text, color, tip = "⚠️", QColor("#FFC107"), f"Status: {status_msg}"
        elif are_equal:
            status_text, color, tip = "✓", QColor("#4CAF50"), "Arquivos equivalentes"
        elif are_equal is False:
            status_text, color, tip = "X", QColor("#F44336"), "Arquivos diferentes"
        else:  # are_equal is None
            status_text, color, tip = "", QColor("gray"), "Sem par para comparação"

        status_item.setText(status_text)
        status_item.setToolTip(tip)
        file_item.setToolTip(tooltip)
        for col in range(table.columnCount()):
            if item := table.item(row, col):
                item.setForeground(color)

    def _on_comparison_finished(self, was_cancelled: bool):
        """Chamado quando a thread de comparação termina."""
        self._set_ui_state(is_running=False)
        self.worker = None
        if was_cancelled:
            logging.warning("A comparação de arquivos foi cancelada pelo utilizador.")
        else:
            show_info("Concluído", "Comparação finalizada.", self)
        QTimer.singleShot(2000, lambda: self.progress_bar.setVisible(False))

    def _clear_all(self):
        """Limpa as tabelas e reseta a UI."""
        if self.worker:
            return
        self.table_a_widget.setRowCount(0)
        self.table_b_widget.setRowCount(0)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)


class FormManager(BaseSingletonFormManager):
    """Gerencia a instância do formulário para garantir que seja um singleton."""

    FORM_CLASS = FormCompararArquivos


def main(parent=None):
    """Ponto de entrada para criar e exibir o formulário."""
    FormManager.show_form(parent)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s"
    )
    main()
    sys.exit(app.exec())
