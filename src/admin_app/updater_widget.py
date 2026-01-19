"""
Widget de atualização para a interface administrativa.
"""

import logging

from PySide6.QtCore import QObject, Qt, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.utils.estilo import aplicar_estilo_botao
from src.utils.update_manager import get_installed_version, run_update_process
from src.utils.utilitarios import (
    aplicar_medida_borda_espaco,
    ask_yes_no,
    show_error,
)
from src.utils.interface_manager import safe_process_events


class UpdateWorker(QObject):
    """Executa o processo de atualização em thread separada."""

    progress = Signal(str, int)
    finished = Signal()
    failed = Signal(str)

    def __init__(self, file_path: str):
        super().__init__()
        self._file_path = file_path

    @Slot()
    def run(self):
        """Executa o update no worker thread e sinaliza progresso/resultado."""
        try:
            run_update_process(self._file_path, self.progress.emit)
            self.finished.emit()
        except Exception as exc:  # pylint: disable=broad-except
            self.failed.emit(str(exc))


class UpdaterWidget(QWidget):
    """Widget para a aba de Atualização."""

    def __init__(self, parent=None):
        """Inicializa o widget de atualização."""
        super().__init__(parent)
        self.selected_file_path = None
        self.file_path_entry = QLineEdit()
        self.version_label = QLabel("")
        self.update_button = QPushButton("Instalar Atualização")
        self.progress_bar = QProgressBar()
        self.progress_view = self._create_progress_view()
        self.main_view = self._create_main_view()
        self.stacked_widget = QStackedWidget()
        self.worker_thread = None
        self.worker = None
        self._setup_ui()
        self._load_current_version()

    def _setup_ui(self):
        """Configura a interface do usuário para o widget de atualização."""
        main_layout = QVBoxLayout(self)
        aplicar_medida_borda_espaco(main_layout, 0, 0)
        self.stacked_widget.addWidget(self.main_view)
        self.stacked_widget.addWidget(self.progress_view)
        main_layout.addWidget(self.stacked_widget)

    def _load_current_version(self):
        """Carrega e exibe a versão atualmente instalada."""
        current_version = get_installed_version()
        self.version_label.setText(
            f"Versão Instalada: {current_version or 'Desconhecida'}"
        )
        self.version_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #0078d4;"
        )

    def _create_main_view(self):
        """Cria a view principal para seleção de arquivo."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        aplicar_medida_borda_espaco(layout, 10, 10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.version_label.setStyleSheet("font-size: 14px; margin-bottom: 15px;")
        layout.addWidget(self.version_label)

        file_group = QGroupBox("Selecionar Pacote de Atualização (.zip)")
        file_layout = QHBoxLayout(file_group)
        aplicar_medida_borda_espaco(file_layout)
        self.file_path_entry.setPlaceholderText("Nenhum arquivo selecionado")
        self.file_path_entry.setToolTip("Caminho do arquivo de atualização selecionado")
        self.file_path_entry.setReadOnly(True)
        file_layout.addWidget(self.file_path_entry)

        select_button = QPushButton("Selecionar...")
        select_button.setToolTip("Selecionar arquivo de atualização (.zip) (Ctrl+O)")
        select_button.setShortcut(QKeySequence("Ctrl+O"))
        aplicar_estilo_botao(select_button, "azul")
        select_button.clicked.connect(self._select_file)
        file_layout.addWidget(select_button)
        layout.addWidget(file_group)

        layout.addStretch()

        self.update_button.setEnabled(False)
        self.update_button.setToolTip("Instalar a atualização selecionada (Ctrl+I)")
        self.update_button.setShortcut(QKeySequence("Ctrl+I"))
        self.update_button.clicked.connect(self.start_update_process)
        aplicar_estilo_botao(self.update_button, "verde")
        layout.addWidget(self.update_button)
        return widget

    def _select_file(self):
        """Abre um diálogo para o usuário selecionar o arquivo de atualização."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Arquivo de Atualização", "", "Arquivos Zip (*.zip)"
        )
        if file_path:
            self.selected_file_path = file_path
            self.file_path_entry.setText(file_path)
            self.update_button.setEnabled(True)
        else:
            self.selected_file_path = None
            self.file_path_entry.clear()
            self.update_button.setEnabled(False)

    def _create_progress_view(self):
        """Cria a view de progresso da atualização."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        aplicar_medida_borda_espaco(layout, 10, 10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_status_label = QLabel("Iniciando atualização...")
        self.progress_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_status_label.setStyleSheet("font-size: 16px;")
        self.progress_bar.setTextVisible(False)
        layout.addStretch(1)
        layout.addWidget(self.progress_status_label)
        layout.addWidget(self.progress_bar)
        layout.addStretch(2)
        return widget

    def _update_progress_ui(self, message: str, value: int):
        """Atualiza a UI de progresso."""
        self.progress_status_label.setText(message)
        self.progress_bar.setValue(value)
        safe_process_events()

    def _reset_widget_state(self):
        """Reseta a interface do widget para o estado inicial após uma atualização."""
        self._load_current_version()
        self.selected_file_path = None
        self.file_path_entry.clear()
        self.update_button.setEnabled(False)
        self.stacked_widget.setCurrentWidget(self.main_view)

    def start_update_process(self):
        """Inicia o processo de atualização da aplicação."""
        if not self.selected_file_path:
            show_error(
                "Erro", "Nenhum arquivo de atualização selecionado.", parent=self
            )
            return

        msg = "A aplicação e suas instâncias serão fechadas. Deseja prosseguir?"
        if not ask_yes_no("Confirmar Atualização", msg, parent=self):
            return

        self.stacked_widget.setCurrentWidget(self.progress_view)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self._start_update_worker()

    def _start_update_worker(self):
        """Inicia o worker em thread separada mantendo a UI responsiva."""
        self.worker_thread = QThread()
        self.worker = UpdateWorker(self.selected_file_path)
        self.worker.moveToThread(self.worker_thread)
        self.worker.progress.connect(self._update_progress_ui)
        self.worker.finished.connect(self._on_update_success)
        self.worker.failed.connect(self._on_update_error)
        self.worker_thread.started.connect(self.worker.run)
        self.worker_thread.start()

    def _on_update_success(self):
        self._update_progress_ui("Concluído!", 100)
        self._cleanup_worker()
        QTimer.singleShot(500, self._reset_widget_state)

    def _on_update_error(self, message: str):
        logging.error("Erro no processo de atualização: %s", message)
        self._cleanup_worker()
        show_error("Erro de Atualização", f"Ocorreu um erro: {message}", parent=self)
        self._reset_widget_state()

    def _cleanup_worker(self):
        QApplication.restoreOverrideCursor()
        if self.worker_thread:
            self.worker_thread.quit()
            self.worker_thread.wait()
            self.worker_thread = None
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
