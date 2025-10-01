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
import shutil
import subprocess  # nosec B404 - necessário para integração com conversores externos
import sys
import tempfile
import traceback
from typing import List, Optional

from PySide6.QtCore import Qt, QThread, QTimer, Signal
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

from src.forms.common.file_tables import StyledFileTableWidget
from src.forms.common.form_manager import BaseSingletonFormManager
from src.forms.common.ui_helpers import (
    attach_actions_with_progress,
    create_dialog_scaffold,
    request_worker_cancel,
    stop_worker_on_error,
    update_processing_state,
)
from src.utils.estilo import (
    aplicar_estilo_botao,
    aplicar_estilo_table_widget,
)
from src.utils.utilitarios import (
    FILE_OPEN_EXCEPTIONS,
    ICON_PATH,
    aplicar_medida_borda_espaco,
    open_file_with_default_app,
    run_trusted_command,
    show_error,
    show_info,
    show_warning,
)

# --- Verificação de Dependências ---
try:
    from PIL import Image, UnidentifiedImageError

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import ezdxf
    import matplotlib.pyplot as plt
    from ezdxf.addons.drawing import Frontend, RenderContext
    from ezdxf.addons.drawing.config import BackgroundPolicy
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

    CAD_LIBS_AVAILABLE = True
except ImportError:
    CAD_LIBS_AVAILABLE = False


def find_external_program(
    program_name: str, executable_name: str, common_paths: List[str]
) -> Optional[str]:
    """
    Tenta encontrar um executável externo no sistema.

    Verifica primeiro o PATH do sistema, depois uma lista de caminhos comuns.
    Retorna o caminho completo do executável se encontrado, senão None.
    """
    # 1. Tenta encontrar no PATH do sistema
    path = shutil.which(executable_name)
    if path and os.path.isfile(path):
        return path

    # 2. Tenta encontrar em diretórios comuns
    for common_path in common_paths:
        # Lógica especial para pastas com versão (ex: ODA File Converter 26.8.0)
        if "*" in common_path:
            base_dir = os.path.dirname(common_path)
            if os.path.isdir(base_dir):
                for item in os.listdir(base_dir):
                    dir_path = os.path.join(base_dir, item)
                    if os.path.isdir(dir_path) and item.startswith(
                        os.path.basename(common_path).replace("*", "")
                    ):
                        full_path = os.path.join(dir_path, executable_name)
                        if os.path.isfile(full_path):
                            return full_path
        else:
            # Caminho padrão sem versão
            full_path = os.path.join(common_path, executable_name)
            if os.path.isfile(full_path):
                return full_path

    logging.warning("'%s' não foi encontrado no sistema.", program_name)
    return None


# --- DETEÇÃO AUTOMÁTICA DE EXECUTÁVEIS ---
INKSCAPE_EXECUTABLE = find_external_program(
    "Inkscape", "inkscape.exe", common_paths=["C:/Program Files/Inkscape/bin"]
)
ODA_CONVERTER_EXECUTABLE = find_external_program(
    "ODA File Converter",
    "ODAFileConverter.exe",
    common_paths=["C:/Program Files/ODA/ODAFileConverter*"],
)

INKSCAPE_AVAILABLE = bool(INKSCAPE_EXECUTABLE)
ODA_CONVERTER_AVAILABLE = bool(ODA_CONVERTER_EXECUTABLE)

# --- Constantes de Configuração ---
LARGURA_FORM_CONVERSAO = 550
ALTURA_FORM_CONVERSAO = 513
MARGEM_LAYOUT_PRINCIPAL = 10

# --- Dicionário de Conversores ---
CONVERSION_HANDLERS = {
    "DWG para PDF": {
        "extensions": ("*.dwg",),
        "tooltip": "Converte DWG para PDF.",
        "enabled": ODA_CONVERTER_AVAILABLE and CAD_LIBS_AVAILABLE,
        "dependency_msg": "O ODA Converter e as bibliotecas ezdxf/matplotlib são necessários.",
    },
    "TIF para PDF": {
        "extensions": ("*.tif", "*.tiff"),
        "tooltip": "Converte TIF para PDF.",
        "enabled": PIL_AVAILABLE,
        "dependency_msg": "A biblioteca 'Pillow' é necessária.",
    },
    "DXF para PDF": {
        "extensions": ("*.dxf",),
        "tooltip": "Converte DXF para PDF.",
        "enabled": CAD_LIBS_AVAILABLE,
        "dependency_msg": "As bibliotecas 'ezdxf' e 'matplotlib' são necessárias.",
    },
    "PDF para DXF": {
        "extensions": ("*.pdf",),
        "tooltip": "Converte PDF para DXF (suporta vetorial e imagem).",
        "enabled": INKSCAPE_AVAILABLE,
        "dependency_msg": "O software Inkscape (instalado e/ou no PATH) é necessário.",
    },
}


class ConversionWorker(QThread):
    """Executa a conversão em segundo plano."""

    progress_percent = Signal(int)
    file_processed = Signal(int, str, bool, str)
    processo_finalizado = Signal(bool)
    error_occurred = Signal(str)

    def __init__(
        self,
        pasta_destino: str,
        files_to_process: list,
        conversion_type: str,
        parent=None,
    ):
        super().__init__(parent)
        self.pasta_destino = pasta_destino
        self.files = files_to_process
        self.conversion_type = conversion_type
        self._is_interrupted = False

    def stop(self):
        """Sinaliza à thread para parar a execução."""
        self._is_interrupted = True

    def run(self):
        """Ponto de entrada da thread, executa o loop de conversão."""
        try:
            total = len(self.files)
            for idx, (row, path_origem) in enumerate(self.files, start=1):
                if self._is_interrupted:
                    break

                if self.conversion_type == "TIF para PDF":
                    self._convert_tif_to_pdf(row, path_origem)
                elif self.conversion_type == "DXF para PDF":
                    self._convert_dxf_to_pdf(row, path_origem, path_origem)
                elif self.conversion_type == "DWG para PDF":
                    self._convert_dwg_to_pdf(row, path_origem)
                elif self.conversion_type == "PDF para DXF":
                    self._convert_pdf_to_dxf(row, path_origem)

                percent = int((idx / total) * 100)
                self.progress_percent.emit(percent)
        except (
            OSError,
            subprocess.CalledProcessError,
            subprocess.TimeoutExpired,
            FileNotFoundError,
        ) as e:
            logging.error("Ocorreu um erro na thread de conversão.")
            logging.error(traceback.format_exc())
            self.error_occurred.emit(f"Ocorreu um erro crítico na conversão:\n{e}")
        finally:
            self.processo_finalizado.emit(self._is_interrupted)

    def _convert_dwg_to_pdf(self, row: int, path_origem: str):
        """Converte DWG para PDF em duas etapas: DWG -> DXF, depois DXF -> PDF."""
        nome_arquivo = os.path.basename(path_origem)
        fd, path_dxf_temp = tempfile.mkstemp(suffix=".dxf", prefix="conv_")
        os.close(fd)

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                command = [
                    ODA_CONVERTER_EXECUTABLE,
                    os.path.dirname(path_origem),
                    temp_dir,
                    "ACAD2018",
                    "DXF",
                    "0",
                    "1",
                    nome_arquivo,
                ]

                # Configuração para execução silenciosa no Windows
                startupinfo = None
                if sys.platform == "win32":
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = subprocess.SW_HIDE  # 0 = Oculto

                run_trusted_command(
                    command,
                    description="ODA Converter DWG->DXF",
                    capture_output=True,
                    timeout=300,
                    startupinfo=startupinfo,
                )

                nome_base = os.path.splitext(nome_arquivo)[0]
                expected_dxf = os.path.join(temp_dir, f"{nome_base}.dxf")
                if os.path.exists(expected_dxf):
                    shutil.move(expected_dxf, path_dxf_temp)
                else:
                    logging.error("FALHA: Arquivo DXF intermediário não foi criado.")
                    raise FileNotFoundError("Arquivo DXF intermediário não foi criado.")

            if self._is_interrupted:
                return

            self._convert_dxf_to_pdf(row, path_dxf_temp, path_origem)

        except (
            subprocess.CalledProcessError,
            subprocess.TimeoutExpired,
            FileNotFoundError,
        ) as e:
            logging.error(
                "FALHA na etapa DWG->DXF para %s.", nome_arquivo, exc_info=True
            )
            msg = f"Falha na etapa DWG->DXF: {getattr(e, 'stderr', e)}"
            self.file_processed.emit(row, "", False, msg)
        finally:
            if os.path.exists(path_dxf_temp):
                os.remove(path_dxf_temp)

    def _convert_tif_to_pdf(self, row: int, path_origem: str):
        """Converte um único arquivo TIF para PDF."""
        nome_arquivo = os.path.basename(path_origem)
        nome_pdf = os.path.splitext(nome_arquivo)[0] + ".pdf"
        path_destino = os.path.join(self.pasta_destino, nome_pdf)
        try:
            with Image.open(path_origem) as img:
                img.convert("RGB").save(path_destino, "PDF")
            self.file_processed.emit(row, path_destino, True, "Conversão bem-sucedida")
        except (IOError, UnidentifiedImageError, OSError) as e:
            logging.error("FALHA na conversão de %s.", nome_arquivo, exc_info=True)
            self.file_processed.emit(row, "", False, str(e))

    def _convert_dxf_to_pdf(
        self, row: int, path_dxf: str, path_original_para_nome: str
    ):
        """
        Converte um arquivo DXF para PDF.
        Usa `path_original_para_nome` para nomear corretamente o arquivo de saída.
        """
        nome_arquivo = os.path.basename(path_original_para_nome)
        nome_base = os.path.splitext(nome_arquivo)[0]
        nome_pdf = nome_base + ".pdf"
        path_destino = os.path.join(self.pasta_destino, nome_pdf)
        try:
            doc = ezdxf.readfile(path_dxf)
            msp = doc.modelspace()
            fig = plt.figure()
            ax = fig.add_axes([0, 0, 1, 1])
            ctx = RenderContext(doc)
            out = MatplotlibBackend(ax)

            frontend = Frontend(ctx, out)
            frontend.config = frontend.config.with_changes(
                background_policy=BackgroundPolicy.WHITE
            )
            frontend.draw_layout(msp, finalize=True)

            fig.savefig(path_destino)
            plt.close(fig)
            self.file_processed.emit(row, path_destino, True, "Conversão bem-sucedida")
        except (IOError, ezdxf.DXFStructureError, OSError) as e:
            logging.error("FALHA na conversão de %s.", nome_arquivo, exc_info=True)
            self.file_processed.emit(row, "", False, str(e))

    def _convert_pdf_to_dxf(self, row: int, path_origem: str):
        """
        Converte PDF para DXF de forma robusta, usando um diretório temporário
        para evitar problemas com caminhos de arquivo complexos.
        """
        nome_arquivo = os.path.basename(path_origem)
        nome_dxf_final = os.path.splitext(nome_arquivo)[0] + ".dxf"
        path_destino_final = os.path.join(self.pasta_destino, nome_dxf_final)

        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Copia o PDF para um nome simples em um caminho simples
                temp_pdf_path = os.path.join(temp_dir, "entrada.pdf")
                shutil.copy(path_origem, temp_pdf_path)

                temp_dxf_path = os.path.join(temp_dir, "saida.dxf")

                # Usa o comando mais simples e compatível
                command = [
                    INKSCAPE_EXECUTABLE,
                    temp_pdf_path,
                    f"--export-filename={temp_dxf_path}",
                    "--pdf-poppler",
                    "--export-text-to-path",
                ]

                result = run_trusted_command(
                    command,
                    description="Inkscape PDF->DXF",
                    capture_output=True,
                    text=True,
                    timeout=180,
                    encoding="utf-8",
                )

                if result.stderr:
                    logging.warning("Saída de Erro (stderr):\n%s", result.stderr)

                if os.path.exists(temp_dxf_path) and os.path.getsize(temp_dxf_path) > 0:
                    # Move o resultado para o destino final
                    shutil.move(temp_dxf_path, path_destino_final)
                    self.file_processed.emit(
                        row, path_destino_final, True, "Conversão bem-sucedida"
                    )
                else:
                    logging.error(
                        "FALHA: Arquivo de saída não foi criado ou está vazio no temp."
                    )
                    raise FileNotFoundError("Arquivo DXF temporário não foi criado.")

            except (
                subprocess.CalledProcessError,
                subprocess.TimeoutExpired,
                FileNotFoundError,
            ) as e:
                logging.error("FALHA na conversão de %s.", nome_arquivo, exc_info=True)
                error_output = "Comando falhou."
                if hasattr(e, "stderr") and e.stderr:
                    error_output = e.stderr
                elif hasattr(e, "stdout") and e.stdout:
                    error_output = e.stdout
                else:
                    error_output = str(e)

                logging.error("Detalhes do erro do subprocesso: %s", error_output)
                msg = f"Erro do Inkscape: {error_output.strip()}"
                self.file_processed.emit(row, "", False, msg)


class FileTableWidget(StyledFileTableWidget):
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
        )

        conteudo = QWidget()
        layout_principal = QVBoxLayout(conteudo)
        aplicar_medida_borda_espaco(layout_principal, MARGEM_LAYOUT_PRINCIPAL)
        vlayout.addWidget(conteudo)

        self._setup_layouts(layout_principal)
        self._on_conversion_type_changed()

    def _setup_layouts(self, main_layout: QVBoxLayout):
        """Cria e organiza os widgets da UI."""
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Tipo de Conversão:"))
        self.cmb_conversion_type = QComboBox()
        self.cmb_conversion_type.addItems(CONVERSION_HANDLERS.keys())
        self.cmb_conversion_type.currentTextChanged.connect(
            self._on_conversion_type_changed
        )
        type_layout.addWidget(self.cmb_conversion_type, 1)
        main_layout.addLayout(type_layout)

        tables_layout = QHBoxLayout()
        self.tabela_origem = FileTableWidget()
        self.tabela_origem.files_added.connect(self._on_files_added)
        self.tabela_resultado = self._criar_tabela_resultado()

        btn_add = QPushButton("➕ Adicionar Arquivos")
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

        action_layout = QHBoxLayout()
        self.btn_converter = QPushButton("🚀 Converter")
        self.btn_converter.clicked.connect(self.executar_conversao)
        aplicar_estilo_botao(self.btn_converter, "verde")
        self.btn_cancel = QPushButton("🛑 Cancelar")
        self.btn_cancel.clicked.connect(self._cancel_conversion)
        self.btn_cancel.setEnabled(False)
        aplicar_estilo_botao(self.btn_cancel, "laranja")
        self.btn_limpar = QPushButton("🧹 Limpar")
        self.btn_limpar.clicked.connect(self._clear_all)
        aplicar_estilo_botao(self.btn_limpar, "vermelho")
        action_layout.addWidget(self.btn_converter)
        action_layout.addWidget(self.btn_limpar)
        action_layout.addWidget(self.btn_cancel)

        self.progress_bar = attach_actions_with_progress(main_layout, action_layout)

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
        btn_destino = QPushButton("📁 Procurar")
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
            file_item.setText(os.path.basename(new_path))
            file_item.setToolTip(new_path)
            file_item.setData(Qt.ItemDataRole.UserRole, new_path)

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
