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

import hashlib
import logging
import os
import subprocess
import sys
import traceback
from typing import List, Optional, Tuple

from PySide6.QtCore import QObject, Qt, QThread, QTimer, Signal
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
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

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

# --- Verificação de Dependências ---
# Tenta importar as bibliotecas da python-occ (STEP/IGES)
try:
    from OCC.Core.BRepGProp import brepgprop
    from OCC.Core.GProp import GProp_GProps
    from OCC.Core.IGESControl import IGESControl_Reader
    from OCC.Core.STEPControl import STEPControl_Reader
    from OCC.Core.TopAbs import TopAbs_EDGE, TopAbs_FACE, TopAbs_VERTEX
    from OCC.Core.TopExp import TopExp_Explorer

    PYTHON_OCC_AVAILABLE = True
except ImportError:
    PYTHON_OCC_AVAILABLE = False

# Tenta importar a biblioteca ezdxf (DXF)
try:
    import ezdxf
    from ezdxf.math import BoundingBox

    EZDXF_AVAILABLE = True
except ImportError:
    EZDXF_AVAILABLE = False

# Tenta importar a biblioteca PyMuPDF (PDF)
try:
    import fitz  # PyMuPDF

    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


# --- Constantes de Configuração ---
LARGURA_FORM = 550
ALTURA_FORM = 513
MARGEM_LAYOUT = 10

# --- Dicionário de Handlers de Arquivo ---
FILE_HANDLERS = {
    "STEP": {
        "extensions": ("*.step", "*.stp"),
        "available": PYTHON_OCC_AVAILABLE,
        "tooltip": "Comparação geométrica de topologia, volume, área, etc.",
    },
    "IGES": {
        "extensions": ("*.igs", "*.iges"),
        "available": PYTHON_OCC_AVAILABLE,
        "tooltip": "Comparação geométrica de topologia, volume, área, etc.",
    },
    "DXF": {
        "extensions": ("*.dxf",),
        "available": EZDXF_AVAILABLE,
        "tooltip": "Comparação por contagem de entidades e extensões do desenho.",
    },
    "PDF": {
        "extensions": ("*.pdf",),
        "available": PYMUPDF_AVAILABLE,
        "tooltip": "Comparação por metadados e hash do conteúdo de texto.",
    },
    "DWG": {
        "extensions": ("*.dwg",),
        "available": True,  # Comparação por hash sempre disponível
        "tooltip": "Comparação por hash binário (identifica se os arquivos são idênticos).",
    },
}


class ComparisonWorker(QThread):
    """Executa a comparação em segundo plano para não bloquear a UI."""

    progress_updated = Signal(int)
    row_compared = Signal(int, object, str, object, str, object)
    comparison_finished = Signal(bool)
    error_occurred = Signal(str)

    def __init__(
        self, files_a: list, files_b: list, file_type: str, parent: QObject = None
    ):
        super().__init__(parent)
        self.files_a = files_a
        self.files_b = files_b
        self.file_type = file_type
        self._is_interrupted = False

    def stop(self):
        """Sinaliza à thread para interromper a execução."""
        self._is_interrupted = True

    # pylint: disable=broad-except
    def run(self):
        """
        Ponto de entrada da thread. Executa o loop de comparação e emite
        sinais para atualizar a UI de forma segura.
        """
        try:
            max_count = max(len(self.files_a), len(self.files_b))
            if max_count == 0:
                self.comparison_finished.emit(self._is_interrupted)
                return

            for i in range(max_count):
                if self._is_interrupted:
                    break

                path_a = self.files_a[i] if i < len(self.files_a) else None
                path_b = self.files_b[i] if i < len(self.files_b) else None

                # Verificação rápida de hash binário
                if path_a and path_b:
                    hash_a = self._get_file_hash(path_a)
                    hash_b = self._get_file_hash(path_b)
                    if hash_a is not None and hash_a == hash_b:
                        props = ("Hash idêntico",)
                        self.row_compared.emit(i, props, "OK", props, "OK", True)
                        continue

                props_a, status_a = (
                    self._get_file_properties(path_a, self.file_type)
                    if path_a
                    else (None, "Sem par")
                )
                props_b, status_b = (
                    self._get_file_properties(path_b, self.file_type)
                    if path_b
                    else (None, "Sem par")
                )
                are_equal = (props_a == props_b) if props_a and props_b else None
                self.row_compared.emit(
                    i, props_a, status_a, props_b, status_b, are_equal
                )

                percent = int(((i + 1) / max_count) * 100)
                self.progress_updated.emit(percent)
        except Exception as e:
            logging.error("Ocorreu um erro inesperado na thread de comparação.")
            logging.error(traceback.format_exc())
            self.error_occurred.emit(f"Ocorreu um erro crítico na comparação:\n{e}")
        finally:
            self.comparison_finished.emit(self._is_interrupted)

    def _get_file_hash(self, file_path: str) -> Optional[str]:
        """Calcula o hash SHA256 do conteúdo de um arquivo."""
        sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256.update(byte_block)
            return sha256.hexdigest()
        except IOError as e:
            logging.warning(
                "Não foi possível calcular o hash para '%s': %s", file_path, e
            )
            return None

    def _get_cad_properties(
        self, file_path: str, reader_class
    ) -> Tuple[Optional[tuple], str]:
        """Lê um arquivo CAD (STEP/IGES) e extrai propriedades geométricas."""
        try:
            reader = reader_class()
            if reader.ReadFile(file_path) != 1:
                msg = f"Falha ao ler o arquivo CAD: {file_path}"
                logging.warning(msg)
                return None, "Erro ao ler o arquivo"
            reader.TransferRoots()
            shape = reader.OneShape()
            if shape is None or shape.IsNull():
                msg = f"Nenhuma geometria encontrada no arquivo: {file_path}"
                logging.warning(msg)
                return None, "Nenhuma geometria encontrada"

            num_faces, num_edges, num_vertices = 0, 0, 0
            explorer = TopExp_Explorer(shape, TopAbs_FACE)
            while explorer.More():
                num_faces += 1
                explorer.Next()
            explorer.Init(shape, TopAbs_EDGE)
            while explorer.More():
                num_edges += 1
                explorer.Next()
            explorer.Init(shape, TopAbs_VERTEX)
            while explorer.More():
                num_vertices += 1
                explorer.Next()

            props_vol, props_surf = GProp_GProps(), GProp_GProps()
            brepgprop.VolumeProperties(shape, props_vol)
            brepgprop.SurfaceProperties(shape, props_surf)
            com = props_vol.CentreOfMass()
            i1, i2, i3 = props_vol.PrincipalProperties().Moments()

            return (
                f"{num_faces} F, {num_edges} A, {num_vertices} V",
                round(props_vol.Mass(), 6),
                round(props_surf.Mass(), 6),
                f"({com.X():.3f}, {com.Y():.3f}, {com.Z():.3f})",
                f"({i1:.3f}, {i2:.3f}, {i3:.3f})",
            ), "OK"
        except (IOError, RuntimeError, ValueError) as e:
            logging.warning("Exceção ao processar arquivo CAD '%s': %s", file_path, e)
            return None, f"Exceção: {e}"

    def _get_dxf_properties(self, file_path: str) -> Tuple[Optional[tuple], str]:
        """Extrai propriedades de um arquivo DXF."""
        try:
            doc = ezdxf.readfile(file_path)
            msp = doc.modelspace()
            bbox = BoundingBox(msp)
            extmin = bbox.extmin if bbox.has_data else (0, 0, 0)
            extmax = bbox.extmax if bbox.has_data else (0, 0, 0)
            return (
                f"{len(msp)} entidades",
                f"({extmin.x:.3f}, {extmin.y:.3f})",
                f"({extmax.x:.3f}, {extmax.y:.3f})",
            ), "OK"
        except (IOError, ezdxf.DXFStructureError) as e:
            logging.warning("Exceção ao processar arquivo DXF '%s': %s", file_path, e)
            return None, f"Exceção: {e}"

    def _get_pdf_properties(self, file_path: str) -> Tuple[Optional[tuple], str]:
        """Extrai propriedades de um arquivo PDF, incluindo um hash de conteúdo robusto."""
        try:
            doc = fitz.open(file_path)
            # pylint: disable=no-member
            metadata = doc.metadata
            content_hash = hashlib.sha256()
            for page in doc:
                content_hash.update(page.get_text("text", sort=True).encode("utf-8"))
                drawings = sorted(
                    page.get_cdrawings(),
                    key=lambda d: (
                        (d["rect"][1], d["rect"][0]) if d.get("rect") else (0, 0)
                    ),
                )
                for drawing in drawings:
                    rect = drawing.get("rect")
                    sig_part = f"type:{drawing.get('type')};"
                    if rect:
                        sig_part += (
                            f"rect:({rect[0]:.2f},{rect[1]:.2f},"
                            f"{rect[2]:.2f},{rect[3]:.2f});"
                        )
                    sig_part += (
                        f"color:{drawing.get('color')};fill:{drawing.get('fill')};"
                        f"w:{drawing.get('width', 0):.2f}"
                    )
                    content_hash.update(sig_part.encode("utf-8"))
            return (
                doc.page_count,
                metadata.get("author", "N/A"),
                metadata.get("creator", "N/A"),
                content_hash.hexdigest(),
            ), "OK"
        except (RuntimeError, ValueError, IOError) as e:
            logging.warning("Exceção ao processar arquivo PDF '%s': %s", file_path, e)
            return None, f"Erro: {e}"

    def _get_file_properties(
        self, file_path: str, file_type: str
    ) -> Tuple[Optional[tuple], str]:
        """Dispatcher que chama a função de extração correta."""
        handlers = {
            "STEP": (self._get_cad_properties, STEPControl_Reader),
            "IGES": (self._get_cad_properties, IGESControl_Reader),
            "DXF": (self._get_dxf_properties,),
            "PDF": (self._get_pdf_properties,),
        }
        if file_type in handlers:
            func, *args = handlers[file_type]
            return func(file_path, *args)
        if file_type == "DWG":
            if file_hash := self._get_file_hash(file_path):
                return (file_hash,), "OK"
            logging.warning("Falha ao calcular hash para arquivo DWG: %s", file_path)
            return None, "Erro ao calcular hash"

        logging.warning("Tipo de arquivo não suportado para extração: %s", file_type)
        return None, "Tipo não suportado"


class FileTableWidget(QTableWidget):
    """Tabela que aceita arquivos arrastados e permite reordenação e exclusão."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        aplicar_estilo_table_widget(self)

        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["#", "Arquivo", "Status"])
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.setColumnWidth(0, 30)
        self.setColumnWidth(2, 45)
        self.verticalHeader().setVisible(False)

        self.other_table: Optional[FileTableWidget] = None
        self.allowed_extensions: List[str] = []
        self.itemDoubleClicked.connect(self._open_file_on_double_click)

    def _open_file_on_double_click(self, item: QTableWidgetItem):
        """Abre o arquivo com o programa padrão do sistema."""
        row = item.row()
        file_item = self.item(row, 1)
        if not file_item:
            return

        file_path = file_item.data(Qt.ItemDataRole.UserRole)
        if not file_path or not os.path.exists(file_path):
            logging.warning("Tentativa de abrir arquivo inexistente: %s", file_path)
            show_warning(
                "Arquivo Não Encontrado",
                f"O arquivo '{os.path.basename(file_path)}' não foi encontrado.",
                parent=self.window(),
            )
            return

        try:
            if sys.platform == "win32":
                os.startfile(file_path)
            elif sys.platform == "darwin":
                subprocess.call(["open", file_path])
            else:
                subprocess.call(["xdg-open", file_path])
        except (OSError, subprocess.CalledProcessError) as e:
            show_error(
                "Erro ao Abrir Arquivo",
                f"Não foi possível abrir o arquivo:\n{e}",
                self.window(),
            )

    def set_other_table(self, other_table: "FileTableWidget"):
        """Define uma referência à outra tabela para verificação de duplicados."""
        self.other_table = other_table

    def set_allowed_extensions(self, extensions: Tuple[str, ...]):
        """Define as extensões de arquivo permitidas."""
        self.allowed_extensions = [ext.replace("*", "") for ext in extensions]

    def _renumber_rows(self):
        """Atualiza a numeração da primeira coluna."""
        for row in range(self.rowCount()):
            self.item(row, 0).setText(str(row + 1))

    def keyPressEvent(self, event):
        """Processa a tecla 'Delete' para remover linhas."""
        if event.key() == Qt.Key.Key_Delete:
            selected_rows = sorted(
                {idx.row() for idx in self.selectedIndexes()}, reverse=True
            )
            for row in selected_rows:
                self.removeRow(row)
            self._renumber_rows()
        else:
            super().keyPressEvent(event)

    def dragEnterEvent(self, event):
        """Aceita o evento se os dados contiverem arquivos permitidos."""
        if event.mimeData().hasUrls() and any(
            url.toLocalFile().lower().endswith(tuple(self.allowed_extensions))
            for url in event.mimeData().urls()
            if url.isLocalFile()
        ):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        """Garante que o cursor mude para indicar uma ação de soltar."""
        event.acceptProposedAction()

    def dropEvent(self, event):
        """Processa os arquivos soltos."""
        files_to_add = [
            url.toLocalFile()
            for url in event.mimeData().urls()
            if url.isLocalFile()
            and url.toLocalFile().lower().endswith(tuple(self.allowed_extensions))
        ]
        if files_to_add:
            self.add_files(files_to_add)

    def add_files(self, file_paths: List[str]):
        """Adiciona arquivos à tabela, evitando duplicados."""
        current_paths = {
            self.item(i, 1).data(Qt.ItemDataRole.UserRole)
            for i in range(self.rowCount())
        }
        other_paths = set()
        if self.other_table:
            other_paths = {
                self.other_table.item(i, 1).data(Qt.ItemDataRole.UserRole)
                for i in range(self.other_table.rowCount())
            }

        all_existing = current_paths.union(other_paths)
        added_count = 0
        for path in file_paths:
            if path not in all_existing:
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
                all_existing.add(path)
                added_count += 1

        skipped_count = len(file_paths) - added_count
        if skipped_count > 0:
            logging.warning("%d arquivo(s) ignorado(s) por duplicidade.", skipped_count)
            show_warning(
                "Arquivos Ignorados",
                f"{skipped_count} arquivo(s) ignorado(s) por já existirem na lista.",
                parent=self.window(),
            )


class FormCompararArquivos(QDialog):
    """Formulário para Comparação de Arquivos."""

    def __init__(self, parent=None):
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
        self.setFixedSize(LARGURA_FORM, ALTURA_FORM)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowIcon(QIcon(ICON_PATH))
        Janela.posicionar_janela(self, "direita")

        vlayout = QVBoxLayout(self)
        aplicar_medida_borda_espaco(vlayout, 0)
        barra = BarraTitulo(self, tema=obter_tema_atual())
        barra.titulo.setText("Comparador de Arquivos")
        vlayout.addWidget(barra)

        conteudo = QWidget()
        layout_principal = QVBoxLayout(conteudo)
        aplicar_medida_borda_espaco(layout_principal, MARGEM_LAYOUT)
        vlayout.addWidget(conteudo)

        self._check_dependencies()
        self._setup_layouts(layout_principal)
        self._on_file_type_changed()

    def _check_dependencies(self):
        """Verifica as dependências e informa o utilizador sobre as que faltam."""
        missing = [
            lib
            for lib, available in [
                ("python-occ-core (para STEP/IGES)", PYTHON_OCC_AVAILABLE),
                ("ezdxf (para DXF)", EZDXF_AVAILABLE),
                ("PyMuPDF (para PDF)", PYMUPDF_AVAILABLE),
            ]
            if not available
        ]
        if missing:
            msg = "Bibliotecas opcionais não encontradas:\n\n- " + "\n- ".join(missing)
            msg += "\n\nFuncionalidades relacionadas estarão desativadas."
            logging.warning("Dependências opcionais ausentes: %s", ", ".join(missing))
            show_info("Dependências Opcionais", msg, parent=self)

    def _setup_layouts(self, main_layout: QVBoxLayout):
        """Configura os layouts internos do formulário."""
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Tipo de Arquivo:"))
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
        lists_layout.addWidget(
            self._create_list_groupbox("Lista A", self.table_a_widget)
        )
        lists_layout.addWidget(
            self._create_list_groupbox("Lista B", self.table_b_widget)
        )
        main_layout.addLayout(lists_layout)

        action_layout = QHBoxLayout()
        self.btn_compare = QPushButton("🔄 Comparar")
        self.btn_compare.clicked.connect(self.iniciar_comparacao)
        aplicar_estilo_botao(self.btn_compare, "verde")
        self.btn_cancel = QPushButton("🛑 Cancelar")
        self.btn_cancel.clicked.connect(self._cancel_comparison)
        self.btn_cancel.setEnabled(False)
        aplicar_estilo_botao(self.btn_cancel, "laranja")
        self.btn_clear = QPushButton("🧹 Limpar")
        self.btn_clear.clicked.connect(self._clear_all)
        aplicar_estilo_botao(self.btn_clear, "vermelho")
        action_layout.addWidget(self.btn_compare)
        action_layout.addWidget(self.btn_cancel)
        action_layout.addWidget(self.btn_clear)
        main_layout.addLayout(action_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

    def _create_list_groupbox(self, title: str, table: FileTableWidget) -> QGroupBox:
        """Cria um QGroupBox contendo uma tabela e um botão de adicionar."""
        groupbox = QGroupBox(title)
        layout = QVBoxLayout(groupbox)
        btn_add = QPushButton(f"➕ Adicionar à {title}")
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
        if self.worker:
            self.btn_cancel.setText("Aguarde...")
            self.btn_cancel.setEnabled(False)
            self.worker.stop()

    def _on_worker_error(self, message: str):
        """Chamado quando um erro não tratado ocorre na thread."""
        if self.worker:
            self.worker.stop()
        show_error("Erro Inesperado na Comparação", message, self)

    def _set_ui_state(self, is_running: bool):
        """Habilita/desabilita controles da UI com base no estado da operação."""
        self.btn_compare.setEnabled(not is_running)
        self.btn_clear.setEnabled(not is_running)
        self.cmb_file_type.setEnabled(not is_running)
        self.btn_cancel.setEnabled(is_running)
        self.progress_bar.setVisible(is_running)
        if is_running:
            self.progress_bar.setValue(0)
        if not is_running:
            self.btn_cancel.setText("🛑 Cancelar")

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
            labels = ["Páginas", "Autor", "Criador", "Hash Conteúdo"]
            lines = [
                f"  - {lbl}: {props[i][:24] if i == 3 else props[i]}..."
                for i, lbl in enumerate(labels)
            ]
        elif file_type == "DWG":
            lines = [f"  - Hash SHA256: {props[0][:32]}..."]
        return header + "\n".join(lines)

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


class FormManager:
    """Gerencia a instância do formulário para garantir que seja um singleton."""

    _instance = None

    @classmethod
    def _reset_instance(cls):
        """Limpa a referência à instância quando o formulário é fechado."""
        cls._instance = None

    @classmethod
    def show_form(cls, parent=None):
        """Cria e exibe o formulário, garantindo uma única instância visível."""
        if cls._instance is None or not cls._instance.isVisible():
            if cls._instance:  # Se existe mas não é visível, pode ter sido fechado
                cls._instance.deleteLater()
            cls._instance = FormCompararArquivos(parent)
            cls._instance.destroyed.connect(cls._reset_instance)
            cls._instance.show()
        else:
            cls._instance.activateWindow()
            cls._instance.raise_()


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
