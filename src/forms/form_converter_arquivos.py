"""
Formulário de Conversão de Arquivos.

Este módulo implementa um formulário para conversão de arquivos, com um layout
inspirado no formulário de comparação para manter a consistência da UI.
Utiliza uma thread para processamento em segundo plano, garantindo que a interface
permaneça responsiva durante a conversão.
"""

# pylint: disable=R0902,R0911,R0913,R0914,R0915,R0917

import logging
import os
import subprocess
import sys
from typing import List, Optional

from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QColor, QIcon
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


# Integração com o ecossistema da aplicação
from src.components.barra_titulo import BarraTitulo
from src.utils.estilo import (
    aplicar_estilo_botao,
    aplicar_estilo_table_widget,
    obter_tema_atual,
)
from src.utils.janelas import Janela
from src.utils.utilitarios import (
    ICON_PATH,
    aplicar_medida_borda_espaco,
    show_error,
    show_info,
    show_warning,
)

# --- Constantes de Configuração ---
LARGURA_FORM_CONVERSAO = 600
ALTURA_FORM_CONVERSAO = 513
MARGEM_LAYOUT_PRINCIPAL = 10

# --- Dicionário de Conversores ---
CONVERSION_HANDLERS = {
    "TIF para PDF": {
        "extensions": ("*.tif", "*.tiff"),
        "tooltip": "Converte arquivos de imagem TIF para o formato PDF.",
        "enabled": PIL_AVAILABLE,
        "dependency_msg": "A biblioteca 'Pillow' é necessária (pip install Pillow).",
    },
    "DXF para PDF": {
        "extensions": ("*.dxf",),
        "tooltip": "Converte arquivos DXF para PDF (requer ezdxf e matplotlib).",
        "enabled": CAD_LIBS_AVAILABLE,
        "dependency_msg": "As bibliotecas 'ezdxf' e 'matplotlib' são necessárias.",
    },
}


class ConversionWorker(QThread):
    """Executa a conversão em segundo plano."""

    progress_percent = Signal(int)
    file_processed = Signal(int, str, bool, str)  # row, new_path, success, message
    processo_finalizado = Signal()

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

    def run(self):
        """Ponto de entrada da thread, executa o loop de conversão."""
        total = len(self.files)
        for idx, (row, path_origem) in enumerate(self.files, start=1):
            if self.conversion_type == "TIF para PDF":
                self._convert_tif_to_pdf(row, path_origem)
            elif self.conversion_type == "DXF para PDF":
                self._convert_dxf_to_pdf(row, path_origem)

            percent = int((idx / total) * 100)
            self.progress_percent.emit(percent)

        self.processo_finalizado.emit()

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
            logging.error("Falha na conversão de TIF '%s': %s", nome_arquivo, e)
            self.file_processed.emit(row, "", False, str(e))

    def _convert_dxf_to_pdf(self, row: int, path_origem: str):
        """Converte um único arquivo DXF para PDF usando ezdxf e matplotlib."""
        nome_arquivo = os.path.basename(path_origem)
        nome_pdf = os.path.splitext(nome_arquivo)[0] + ".pdf"
        path_destino = os.path.join(self.pasta_destino, nome_pdf)
        try:
            doc = ezdxf.readfile(path_origem)
            msp = doc.modelspace()

            fig = plt.figure()
            ax = fig.add_axes([0, 0, 1, 1])
            ax.set_facecolor("#FFFFFF")

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
            logging.error("Falha na conversão de DXF '%s': %s", nome_arquivo, e)
            self.file_processed.emit(row, "", False, str(e))


class FileTableWidget(QTableWidget):
    """Tabela personalizada para exibir arquivos, suportando arrastar e soltar."""

    files_added = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        aplicar_estilo_table_widget(self)
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["#", "Arquivo"])
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.setColumnWidth(0, 30)
        self.verticalHeader().setVisible(False)
        self.allowed_extensions = []

    def set_allowed_extensions(self, extensions: List[str]):
        """Define as extensões de arquivo permitidas para arrastar e soltar."""
        self.allowed_extensions = [ext.replace("*", "") for ext in extensions]

    # pylint: disable=invalid-name
    def dragEnterEvent(self, event):
        """Valida se os arquivos arrastados têm a extensão permitida."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(
                url.toLocalFile().lower().endswith(tuple(self.allowed_extensions))
                for url in urls
                if url.isLocalFile()
            ):
                event.acceptProposedAction()

    # pylint: disable=invalid-name
    def dragMoveEvent(self, event):
        """Aceita o movimento de arrastar."""
        event.acceptProposedAction()

    # pylint: disable=invalid-name
    def dropEvent(self, event):
        """Adiciona os arquivos soltos à tabela."""
        files_to_add = [
            url.toLocalFile()
            for url in event.mimeData().urls()
            if url.isLocalFile()
            and url.toLocalFile().lower().endswith(tuple(self.allowed_extensions))
        ]
        if files_to_add:
            self.add_files(files_to_add)

    def add_files(self, file_paths: List[str]):
        """Adiciona uma lista de caminhos de arquivo à tabela, evitando duplicatas."""
        current_paths = {
            self.item(i, 1).data(Qt.ItemDataRole.UserRole)
            for i in range(self.rowCount())
        }
        newly_added_paths = []
        for path in file_paths:
            if path not in current_paths:
                row = self.rowCount()
                self.insertRow(row)
                num_item = QTableWidgetItem(str(row + 1))
                num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                file_item = QTableWidgetItem(os.path.basename(path))
                file_item.setData(Qt.ItemDataRole.UserRole, path)
                file_item.setToolTip(path)
                self.setItem(row, 0, num_item)
                self.setItem(row, 1, file_item)
                newly_added_paths.append(path)

        if newly_added_paths:
            self.files_added.emit(newly_added_paths)


class FormConverterArquivos(QDialog):
    """Formulário para Conversão de Arquivos."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker: Optional[ConversionWorker] = None

        # Inicialização dos atributos da UI para conformidade com Pylint
        self.cmb_conversion_type: Optional[QComboBox] = None
        self.tabela_origem: Optional[FileTableWidget] = None
        self.tabela_resultado: Optional[QTableWidget] = None
        self.destino_entry: Optional[QLineEdit] = None
        self.btn_converter: Optional[QPushButton] = None
        self.btn_limpar: Optional[QPushButton] = None
        self.progress_bar: Optional[QProgressBar] = None

        self._inicializar_ui()

    def _inicializar_ui(self):
        """Configura a interface gráfica do formulário."""
        self.setWindowTitle("Conversor de Arquivos")
        self.setFixedSize(LARGURA_FORM_CONVERSAO, ALTURA_FORM_CONVERSAO)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowIcon(QIcon(ICON_PATH))
        Janela.posicionar_janela(self, "direita")

        vlayout = QVBoxLayout(self)
        vlayout.setContentsMargins(0, 0, 0, 0)
        vlayout.setSpacing(0)
        barra = BarraTitulo(self, tema=obter_tema_atual())
        barra.titulo.setText("Conversor de Arquivos")
        vlayout.addWidget(barra)

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
        for name, _ in CONVERSION_HANDLERS.items():
            self.cmb_conversion_type.addItem(name)
        self.cmb_conversion_type.currentTextChanged.connect(
            self._on_conversion_type_changed
        )
        type_layout.addWidget(self.cmb_conversion_type, 1)
        main_layout.addLayout(type_layout)

        tables_layout = QHBoxLayout()
        self.tabela_origem = FileTableWidget()
        self.tabela_origem.files_added.connect(self._on_files_added)

        self.tabela_resultado = QTableWidget()
        aplicar_estilo_table_widget(self.tabela_resultado)
        self.tabela_resultado.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.tabela_resultado.itemDoubleClicked.connect(self._abrir_arquivo_resultado)
        self.tabela_resultado.setColumnCount(3)
        self.tabela_resultado.setHorizontalHeaderLabels(["#", "Arquivo", "Status"])
        self.tabela_resultado.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Fixed
        )
        self.tabela_resultado.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.tabela_resultado.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Fixed
        )
        self.tabela_resultado.setColumnWidth(0, 30)
        self.tabela_resultado.setColumnWidth(2, 45)
        self.tabela_resultado.verticalHeader().setVisible(False)

        btn_add = QPushButton("➕ Adicionar Arquivos")
        btn_add.clicked.connect(lambda: self._select_files(self.tabela_origem))
        aplicar_estilo_botao(btn_add, "cinza")

        self.destino_entry = QLineEdit()
        self.destino_entry.setPlaceholderText("Pasta de Destino...")
        btn_destino = QPushButton("📁 Procurar")
        btn_destino.clicked.connect(self._selecionar_pasta_destino)
        aplicar_estilo_botao(btn_destino, "cinza")
        destino_widget = QWidget()
        destino_layout = QHBoxLayout(destino_widget)
        destino_layout.setContentsMargins(0, 0, 0, 0)
        destino_layout.addWidget(self.destino_entry)
        destino_layout.addWidget(btn_destino)

        tables_layout.addWidget(
            self._criar_tabela_groupbox(
                "Arquivos de Origem", self.tabela_origem, btn_add
            )
        )
        tables_layout.addWidget(
            self._criar_tabela_groupbox(
                "Resultado da Conversão", self.tabela_resultado, destino_widget
            )
        )
        main_layout.addLayout(tables_layout, 1)

        action_layout = QHBoxLayout()
        self.btn_converter = QPushButton("🚀 Converter")
        self.btn_converter.clicked.connect(self.executar_conversao)
        aplicar_estilo_botao(self.btn_converter, "verde")
        self.btn_limpar = QPushButton("🧹 Limpar Tudo")
        self.btn_limpar.clicked.connect(self._clear_all)
        aplicar_estilo_botao(self.btn_limpar, "vermelho")
        action_layout.addWidget(self.btn_converter)
        action_layout.addWidget(self.btn_limpar)
        main_layout.addLayout(action_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

    def _criar_tabela_groupbox(self, title, table_widget, top_widget):
        """Cria um QGroupBox com um widget superior e uma tabela."""
        gb = QGroupBox(title)
        layout = QVBoxLayout(gb)
        if top_widget:
            layout.addWidget(top_widget)
        layout.addWidget(table_widget)
        return gb

    def _on_files_added(self, added_paths: List[str]):
        """Define a pasta de destino com base no primeiro arquivo adicionado."""
        if not self.destino_entry.text() and added_paths:
            primeiro_arquivo = added_paths[0]
            pasta_destino = os.path.dirname(primeiro_arquivo)
            self.destino_entry.setText(pasta_destino)

    def _abrir_arquivo_resultado(self, item: QTableWidgetItem):
        """Abre o arquivo correspondente ao item da tabela de resultados."""
        if item.column() != 1:
            return

        caminho_arquivo = item.data(Qt.ItemDataRole.UserRole)
        if caminho_arquivo and os.path.exists(caminho_arquivo):
            try:
                if sys.platform == "win32":
                    os.startfile(caminho_arquivo)
                elif sys.platform == "darwin":  # macOS
                    subprocess.call(("open", caminho_arquivo))
                else:  # linux
                    subprocess.call(("xdg-open", caminho_arquivo))
            except (OSError, FileNotFoundError) as e:
                show_error(
                    "Erro ao Abrir", f"Não foi possível abrir o arquivo:\n{e}", self
                )
        else:
            status_item = self.tabela_resultado.item(item.row(), 2)
            if status_item and status_item.text() == "✓":
                show_warning("Aviso", "O arquivo convertido não foi encontrado.", self)

    def _on_conversion_type_changed(self):
        """Atualiza a UI quando o tipo de conversão é alterado."""
        self._clear_all()
        conv_type = self.cmb_conversion_type.currentText()
        handler = CONVERSION_HANDLERS.get(conv_type)
        if handler:
            self.tabela_origem.set_allowed_extensions(handler["extensions"])
            self.btn_converter.setToolTip(handler["tooltip"])
            self.btn_converter.setEnabled(handler["enabled"])
            if not handler["enabled"]:
                show_warning("Dependência Faltando", handler["dependency_msg"], self)

    def _selecionar_pasta_destino(self):
        """Abre um diálogo para selecionar a pasta de destino."""
        diretorio = QFileDialog.getExistingDirectory(
            self, "Selecionar Pasta de Destino"
        )
        if diretorio:
            self.destino_entry.setText(diretorio)

    def _select_files(self, table_widget):
        """Abre um diálogo para selecionar os arquivos de origem."""
        conv_type = self.cmb_conversion_type.currentText()
        handler = CONVERSION_HANDLERS.get(conv_type)
        if not handler:
            return

        extensions = " ".join(handler["extensions"])
        dialog_filter = f"Arquivos ({extensions});;Todos os arquivos (*)"
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Selecionar Arquivos", "", dialog_filter
        )
        if file_paths:
            table_widget.add_files(file_paths)

    def _clear_all(self):
        """Limpa todas as tabelas e campos de entrada."""
        self.tabela_origem.setRowCount(0)
        self.tabela_resultado.setRowCount(0)
        self.destino_entry.clear()
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)

    def executar_conversao(self):
        """Inicia o processo de conversão dos arquivos."""
        conv_type = self.cmb_conversion_type.currentText()
        handler = CONVERSION_HANDLERS.get(conv_type)
        if not handler or not handler["enabled"]:
            self._on_conversion_type_changed()
            return

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

        self.btn_converter.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.tabela_resultado.setRowCount(0)

        files_to_process = []
        for row in range(self.tabela_origem.rowCount()):
            item = self.tabela_origem.item(row, 1)
            full_path = item.data(Qt.ItemDataRole.UserRole)
            files_to_process.append((row, full_path))

            self.tabela_resultado.insertRow(row)
            self.tabela_resultado.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            self.tabela_resultado.setItem(row, 1, QTableWidgetItem(item.text()))
            self.tabela_resultado.setItem(row, 2, QTableWidgetItem("..."))

        self.worker = ConversionWorker(
            self.destino_entry.text(), files_to_process, conv_type
        )
        self.worker.progress_percent.connect(self.progress_bar.setValue)
        self.worker.file_processed.connect(self._update_file_status)
        self.worker.processo_finalizado.connect(self._on_conversion_finished)
        self.worker.start()

    def _update_file_status(self, row, new_path, success, message):
        """Atualiza o status de um arquivo na tabela de resultados."""
        status_item = QTableWidgetItem()
        status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        color = QColor("#4CAF50") if success else QColor("#F44336")
        status_item.setText("✓" if success else "✗")
        status_item.setForeground(color)
        status_item.setToolTip(message)
        self.tabela_resultado.setItem(row, 2, status_item)

        file_item = self.tabela_resultado.item(row, 1)
        if success:
            file_item.setText(os.path.basename(new_path))
            file_item.setToolTip(new_path)
            file_item.setData(Qt.ItemDataRole.UserRole, new_path)

    def _on_conversion_finished(self):
        """Executado quando a thread de conversão termina."""
        self.btn_converter.setEnabled(True)
        show_info("Sucesso", "Conversão de arquivos finalizada.", self)
        QTimer.singleShot(2000, lambda: self.progress_bar.setVisible(False))


class FormManager:
    """Gerencia a instância do formulário para evitar múltiplas janelas."""

    _instance = None

    @classmethod
    def _reset_instance(cls):
        """Reseta a instância quando o formulário é fechado."""
        cls._instance = None

    @classmethod
    def show_form(cls, parent=None):
        """Mostra o formulário, criando uma nova instância se necessário."""
        if cls._instance is None:
            cls._instance = FormConverterArquivos(parent)
            cls._instance.destroyed.connect(cls._reset_instance)
            cls._instance.show()
        else:
            cls._instance.activateWindow()
            cls._instance.raise_()


def main(parent=None):
    """Função principal para exibir o formulário."""
    FormManager.show_form(parent)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main()
    sys.exit(app.exec())
