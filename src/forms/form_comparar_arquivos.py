"""
Módulo para o formulário de Comparador Geométrico de Arquivos.

Este formulário permite aos utilizadores carregar arquivos (STEP, IGES, PDF, DXF, DWG)
em duas listas lado a lado e realizar uma comparação detalhada.
A comparação utiliza bibliotecas específicas para cada tipo de arquivo para
extrair e comparar propriedades relevantes.
"""

# pylint: disable=R0911,R0913,R0914,R0917

import hashlib
import logging
import os
import subprocess
import sys
from typing import Optional

from PySide6.QtCore import Qt, QTimer
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
from src.config import globals as g
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


class FileTableWidget(QTableWidget):
    """
    Tabela personalizada que aceita arquivos arrastados e soltos,
    mostra uma numeração, impede duplicados e permite reordenação de itens.
    """

    def __init__(self, parent=None):
        """Inicializa o widget da tabela."""
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # Aplicar estilo de grade visual
        aplicar_estilo_table_widget(self)

        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["#", "Arquivo", "Status"])
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.setColumnWidth(0, 10)
        self.setColumnWidth(2, 45)
        self.verticalHeader().setVisible(False)

        self.other_table = None
        self.allowed_extensions = []

        # Conecta o sinal de duplo clique ao método de abrir arquivo
        self.itemDoubleClicked.connect(self._open_file_on_double_click)

    def _open_file_on_double_click(self, item):
        """
        Abre o arquivo associado à linha que recebeu o duplo clique com
        o programa padrão do sistema operacional.
        """
        row = item.row()
        file_item = self.item(row, 1)  # A coluna 1 contém o nome do arquivo
        if not file_item:
            return

        file_path = file_item.data(Qt.ItemDataRole.UserRole)
        if not file_path or not os.path.exists(file_path):
            mensagem_erro_abr = (
                f"O arquivo '{os.path.basename(file_path)}' não foi encontrado "
                "no caminho especificado."
            )
            show_warning(
                "Arquivo Não Encontrado", mensagem_erro_abr, parent=self.window()
            )
            return

        try:
            if sys.platform == "win32":
                os.startfile(file_path)
            elif sys.platform == "darwin":  # macOS
                subprocess.call(["open", file_path])
            else:  # linux variants
                subprocess.call(["xdg-open", file_path])
        except (OSError, subprocess.CalledProcessError) as e:
            mensagem_erro_abr = (
                f"Não foi possível abrir o arquivo '{os.path.basename(file_path)}'.\n\n"
                f"Verifique se há um programa padrão associado a esta extensão.\n"
                f"Detalhes do erro: {e}"
            )
            show_error("Erro ao Abrir Arquivo", mensagem_erro_abr, parent=self.window())

    def set_other_table(self, other_table_widget):
        """Define uma referência à outra tabela para verificação de duplicados."""
        self.other_table = other_table_widget

    def set_allowed_extensions(self, extensions):
        """Define as extensões de arquivo permitidas para arrastar e soltar."""
        self.allowed_extensions = [ext.replace("*", "") for ext in extensions]

    def _renumber_rows(self):
        """Atualiza a numeração da primeira coluna após uma alteração."""
        for row in range(self.rowCount()):
            self.item(row, 0).setText(str(row + 1))

    # pylint: disable=invalid-name
    def keyPressEvent(self, event):
        """Processa o evento de pressionar a tecla 'Delete' para remover linhas."""
        if event.key() == Qt.Key.Key_Delete:
            selected_rows = sorted(
                list(set(index.row() for index in self.selectedIndexes())), reverse=True
            )
            if not selected_rows:
                return

            for row in selected_rows:
                self.removeRow(row)

            self._renumber_rows()
        else:
            super().keyPressEvent(event)

    # pylint: disable=invalid-name
    def dragEnterEvent(self, event):
        """Aceita o evento de arrastar se os dados contiverem arquivos permitidos."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(
                url.toLocalFile().lower().endswith(tuple(self.allowed_extensions))
                for url in urls
                if url.isLocalFile()
            ):
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()

    # pylint: disable=invalid-name
    def dragMoveEvent(self, event):
        """Garante que o cursor mude para indicar uma ação de soltar."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    # pylint: disable=invalid-name
    def dropEvent(self, event):
        """Processa os arquivos soltos, filtrando pela extensão permitida."""
        files_to_add = [
            url.toLocalFile()
            for url in event.mimeData().urls()
            if url.isLocalFile()
            and url.toLocalFile().lower().endswith(tuple(self.allowed_extensions))
        ]
        if files_to_add:
            self.add_files(files_to_add)

    def add_files(self, file_paths):
        """Adiciona uma lista de caminhos de arquivo à tabela, evitando duplicados."""
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

        all_existing_paths = current_paths.union(other_paths)
        skipped_count = 0

        for path in file_paths:
            if path not in all_existing_paths:
                row_position = self.rowCount()
                self.insertRow(row_position)
                num_item = QTableWidgetItem(str(row_position + 1))
                num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                status_item = QTableWidgetItem("")
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                file_item = QTableWidgetItem(os.path.basename(path))
                file_item.setData(Qt.ItemDataRole.UserRole, path)
                file_item.setToolTip(path)
                self.setItem(row_position, 0, num_item)
                self.setItem(row_position, 1, file_item)
                self.setItem(row_position, 2, status_item)
                all_existing_paths.add(path)
            else:
                skipped_count += 1
        if skipped_count > 0:
            show_warning(
                "Arquivos Ignorados",
                f"{skipped_count} arquivo(s) não foram adicionados porque já existem.",
                parent=self.window(),
            )


class FormCompararArquivos(QDialog):
    """Formulário para Comparação de Arquivos."""

    def __init__(self, parent=None):
        """Inicializa o formulário."""
        super().__init__(parent)
        self.table_a_widget: Optional[FileTableWidget] = None
        self.table_b_widget: Optional[FileTableWidget] = None
        self.progress_bar: Optional[QProgressBar] = None
        self.btn_compare: Optional[QPushButton] = None
        self.btn_clear: Optional[QPushButton] = None
        self.cmb_file_type: Optional[QComboBox] = None
        self._inicializar_ui()

    def _inicializar_ui(self):
        """Inicializa a interface do utilizador."""
        self.setFixedSize(LARGURA_FORM, ALTURA_FORM)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
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
        self._on_file_type_changed()  # Configura o estado inicial

    def _check_dependencies(self):
        """Verifica as dependências e informa o utilizador sobre as que faltam."""
        missing = []
        if not PYTHON_OCC_AVAILABLE:
            missing.append("python-occ-core (para STEP/IGES)")
        if not EZDXF_AVAILABLE:
            missing.append("ezdxf (para DXF)")
        if not PYMUPDF_AVAILABLE:
            missing.append("PyMuPDF (para PDF)")

        if missing:
            mensagem_erro_bibl = "As seguintes bibliotecas não foram encontradas:\n\n"
            mensagem_erro_bibl += "\n".join(f"- {lib}" for lib in missing)
            mensagem_erro_bibl += (
                "\n\nFuncionalidades relacionadas estarão desativadas."
            )
            show_info("Bibliotecas Opcionais Faltando", mensagem_erro_bibl, parent=self)

    def _setup_layouts(self, main_layout: QVBoxLayout):
        """Configura os layouts internos do formulário."""
        # Layout do Seletor de Tipo de Arquivo
        type_selector_layout = QHBoxLayout()
        type_selector_layout.addWidget(QLabel("Tipo de Arquivo:"))
        self.cmb_file_type = QComboBox()
        for name, data in FILE_HANDLERS.items():
            if data["available"]:
                self.cmb_file_type.addItem(name)
        self.cmb_file_type.setToolTip(
            "Selecione o tipo de arquivo para comparar.\nAs listas serão limpas ao trocar."
        )
        self.cmb_file_type.currentTextChanged.connect(self._on_file_type_changed)
        type_selector_layout.addWidget(self.cmb_file_type, 1)
        main_layout.addLayout(type_selector_layout)

        # Layout das Listas de Arquivos
        lists_layout = QHBoxLayout()
        self.table_a_widget = FileTableWidget()
        self.table_b_widget = FileTableWidget()
        self.table_a_widget.set_other_table(self.table_b_widget)
        self.table_b_widget.set_other_table(self.table_a_widget)

        list_a_gb = self._create_list_groupbox(
            "Lista A", self.table_a_widget, "➕ Adicionar à Lista A"
        )
        list_b_gb = self._create_list_groupbox(
            "Lista B", self.table_b_widget, "➕ Adicionar à Lista B"
        )
        lists_layout.addWidget(list_a_gb)
        lists_layout.addWidget(list_b_gb)
        main_layout.addLayout(lists_layout)

        # Layout dos Botões de Ação
        action_layout = QHBoxLayout()
        self.btn_compare = QPushButton("🔄 Comparar Arquivos")
        self.btn_compare.clicked.connect(self._compare_files)
        aplicar_estilo_botao(self.btn_compare, "verde")
        self.btn_clear = QPushButton("🧹 Limpar Tudo")
        self.btn_clear.clicked.connect(self._clear_all)
        aplicar_estilo_botao(self.btn_clear, "vermelho")
        action_layout.addWidget(self.btn_compare)
        action_layout.addWidget(self.btn_clear)
        main_layout.addLayout(action_layout)

        # Barra de Progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setToolTip("Progresso da comparação")
        main_layout.addWidget(self.progress_bar)

    def _create_list_groupbox(self, title, table_widget, btn_text):
        """Cria um QGroupBox contendo uma tabela e um botão de adicionar."""
        groupbox = QGroupBox(title)
        layout = QVBoxLayout(groupbox)
        btn_add = QPushButton(btn_text)
        btn_add.clicked.connect(lambda: self._select_files(table_widget))
        aplicar_estilo_botao(btn_add, "cinza")
        layout.addWidget(btn_add)
        layout.addWidget(table_widget)
        aplicar_medida_borda_espaco(layout, 5)
        return groupbox

    def _on_file_type_changed(self):
        """Chamado quando o tipo de arquivo no ComboBox muda."""
        self._clear_all()
        file_type = self.cmb_file_type.currentText()
        handler = FILE_HANDLERS.get(file_type)
        if handler:
            extensions = handler["extensions"]
            self.table_a_widget.set_allowed_extensions(extensions)
            self.table_b_widget.set_allowed_extensions(extensions)
            self.btn_compare.setToolTip(handler["tooltip"])

    def _select_files(self, table_widget):
        """Abre uma caixa de diálogo para selecionar arquivos com base no tipo."""
        file_type = self.cmb_file_type.currentText()
        handler = FILE_HANDLERS.get(file_type)
        if not handler:
            return

        extensions = " ".join(handler["extensions"])
        dialog_filter = f"{file_type} Files ({extensions});;All Files (*)"

        file_paths, _ = QFileDialog.getOpenFileNames(
            self, f"Selecionar Arquivos {file_type}", "", dialog_filter
        )
        if file_paths:
            table_widget.add_files(file_paths)

    def _get_file_hash(self, file_path):
        """Calcula o hash SHA256 do conteúdo de um arquivo."""
        sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256.update(byte_block)
            return sha256.hexdigest()
        except IOError as e:
            logging.error(
                "Falha ao ler o arquivo para calcular o hash: %s",
                file_path,
                exc_info=e,
            )
            return None

    # --- Funções de Extração de Propriedades ---

    def _get_cad_properties(self, file_path, reader_class):
        """Lê um arquivo CAD (STEP/IGES) e extrai propriedades geométricas."""
        try:
            reader = reader_class()
            if reader.ReadFile(file_path) != 1:
                return None, "Erro ao ler o arquivo"
            reader.TransferRoots()
            shape = reader.OneShape()
            if shape is None or shape.IsNull():
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

            props_vol = GProp_GProps()
            brepgprop.VolumeProperties(shape, props_vol)
            com = props_vol.CentreOfMass()
            i1, i2, i3 = props_vol.PrincipalProperties().Moments()

            props_surf = GProp_GProps()
            brepgprop.SurfaceProperties(shape, props_surf)

            return (
                f"{num_faces} Faces, {num_edges} Arestas, {num_vertices} Vértices",
                round(props_vol.Mass(), 6),
                round(props_surf.Mass(), 6),
                f"({round(com.X(), 3)}, {round(com.Y(), 3)}, {round(com.Z(), 3)})",
                f"({round(i1, 3)}, {round(i2, 3)}, {round(i3, 3)})",
            ), "OK"
        except (IOError, RuntimeError) as e:
            logging.error(
                "Falha ao processar arquivo CAD '%s': %s",
                os.path.basename(file_path),
                e,
            )
            return None, f"Exceção: {str(e)}"

    def _get_dxf_properties(self, file_path):
        """Extrai propriedades de um arquivo DXF."""
        try:
            doc = ezdxf.readfile(file_path)
            msp = doc.modelspace()
            bbox = BoundingBox(msp)
            extmin = bbox.extmin if bbox.has_data else (0, 0, 0)
            extmax = bbox.extmax if bbox.has_data else (0, 0, 0)
            return (
                f"{len(msp)} entidades",
                f"({round(extmin.x, 3)}, {round(extmin.y, 3)})",
                f"({round(extmax.x, 3)}, {round(extmax.y, 3)})",
            ), "OK"
        except (IOError, ezdxf.DXFStructureError) as e:
            logging.error(
                "Falha ao processar arquivo DXF '%s': %s",
                os.path.basename(file_path),
                e,
            )
            return None, f"Exceção: {str(e)}"

    def _get_pdf_properties(self, file_path):
        """
        Extrai propriedades de um arquivo PDF, gerando um hash de conteúdo robusto
        que inclui texto, metadados e uma "impressão digital" dos desenhos vetoriais.
        """
        try:
            doc = fitz.open(file_path)
            # pylint: disable=no-member
            metadata = doc.metadata
            page_count = doc.page_count
            content_hash = hashlib.sha256()

            for page in doc:
                # 1. Adiciona texto ao hash (ordenado para consistência)
                content_hash.update(page.get_text("text", sort=True).encode("utf-8"))

                # 2. Adiciona uma "impressão digital" dos desenhos vetoriais
                # get_cdrawings() é mais estável e limpa os dados para nós.
                drawings = page.get_cdrawings()

                # Ordena os desenhos por sua posição (y, depois x) para garantir
                # uma ordem consistente, independentemente de como o PDF os armazena.
                drawings.sort(
                    key=lambda d: (
                        (d["rect"][1], d["rect"][0]) if d.get("rect") else (0, 0)
                    )
                )

                drawing_signature = []
                for drawing in drawings:
                    rect = drawing.get("rect")
                    color = drawing.get("color")
                    fill = drawing.get("fill")
                    width = drawing.get("width", 0)

                    # Cria uma string representativa para cada desenho.
                    # Arredondar valores de ponto flutuante é crucial para evitar
                    # pequenas diferenças irrelevantes.
                    if rect:
                        sig_part = (
                            f"type:{drawing.get('type')};"
                            f"rect:({rect[0]:.2f},{rect[1]:.2f},{rect[2]:.2f},{rect[3]:.2f});"
                        )
                        sig_part += f"color:{color};fill:{fill};w:{width:.2f}"
                        drawing_signature.append(sig_part)

                # Concatena todas as assinaturas de desenho da página e atualiza o hash
                content_hash.update("".join(drawing_signature).encode("utf-8"))

            full_hash = content_hash.hexdigest()

            return (
                page_count,
                metadata.get("author", "N/A"),
                metadata.get("creator", "N/A"),
                full_hash,
            ), "OK"
        except (RuntimeError, ValueError, IOError) as e:
            # Se ocorrer qualquer erro durante a análise, informa o utilizador.
            logging.error(
                "Falha ao processar PDF '%s': %s", os.path.basename(file_path), e
            )
            return None, f"Erro ao processar PDF: {str(e)}"

    def _get_file_properties(self, file_path, file_type):
        """Dispatcher que chama a função de extração correta para o tipo de arquivo."""
        if file_type == "STEP":
            return self._get_cad_properties(file_path, STEPControl_Reader)
        if file_type == "IGES":
            return self._get_cad_properties(file_path, IGESControl_Reader)
        if file_type == "DXF":
            return self._get_dxf_properties(file_path)
        if file_type == "PDF":
            return self._get_pdf_properties(file_path)
        if file_type == "DWG":
            file_hash = self._get_file_hash(file_path)
            if file_hash:
                return (file_hash,), "OK"
            return None, "Erro ao calcular hash"
        return None, "Tipo de arquivo não suportado"

    def _compare_files(self):
        """Inicia o processo de comparação para todos os arquivos nas listas."""
        if self.table_a_widget.rowCount() == 0 or self.table_b_widget.rowCount() == 0:
            show_warning("Aviso", "Adicione arquivos em ambas as listas.", parent=self)
            return

        # Limpa os status anteriores para indicar o início de uma nova comparação
        for row in range(self.table_a_widget.rowCount()):
            if item := self.table_a_widget.item(row, 2):
                item.setText("")
        for row in range(self.table_b_widget.rowCount()):
            if item := self.table_b_widget.item(row, 2):
                item.setText("")

        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.btn_compare.setEnabled(False)
        self.btn_clear.setEnabled(False)
        QApplication.processEvents()  # Garante que a UI seja atualizada antes de começar

        file_type = self.cmb_file_type.currentText()

        try:
            max_count = max(
                self.table_a_widget.rowCount(), self.table_b_widget.rowCount()
            )

            for i in range(max_count):
                item_a = self.table_a_widget.item(i, 1)
                item_b = self.table_b_widget.item(i, 1)
                path_a = item_a.data(Qt.ItemDataRole.UserRole) if item_a else None
                path_b = item_b.data(Qt.ItemDataRole.UserRole) if item_b else None

                if path_a and path_b:
                    hash_a = self._get_file_hash(path_a)
                    hash_b = self._get_file_hash(path_b)
                    if hash_a is not None and hash_a == hash_b:
                        self._update_row_status(
                            self.table_a_widget,
                            i,
                            ("Hash idêntico",),
                            "OK",
                            True,
                        )
                        self._update_row_status(
                            self.table_b_widget,
                            i,
                            ("Hash idêntico",),
                            "OK",
                            True,
                        )
                        continue

                props_a, status_a = (
                    self._get_file_properties(path_a, file_type)
                    if path_a
                    else (None, "Sem par")
                )
                props_b, status_b = (
                    self._get_file_properties(path_b, file_type)
                    if path_b
                    else (None, "Sem par")
                )

                are_equal = (props_a == props_b) if props_a and props_b else None

                if item_a:
                    self._update_row_status(
                        self.table_a_widget, i, props_a, status_a, are_equal
                    )
                if item_b:
                    self._update_row_status(
                        self.table_b_widget, i, props_b, status_b, are_equal
                    )

                percent = int(((i + 1) / max_count) * 100)
                self.progress_bar.setValue(percent)
                QApplication.processEvents()

        finally:
            self.btn_compare.setEnabled(True)
            self.btn_clear.setEnabled(True)
            QTimer.singleShot(2000, lambda: self.progress_bar.setVisible(False))

    def _format_properties_tooltip(self, props, file_type):
        """Formata o texto das propriedades para a tooltip com base no tipo de arquivo."""
        if not props:
            return ""

        # Trata o caso especial de hash binário primeiro para evitar erros
        if props and props[0] == "Hash idêntico":
            return "\n\nDados idênticos (correspondência de hash binário)."

        header = "\n\nPropriedades Extraídas:\n"
        lines = []

        if file_type in ("STEP", "IGES"):
            labels = [
                "Topologia",
                "Volume",
                "Área de Sup.",
                "Centro de Massa",
                "Mom. Inércia",
            ]
            lines = [f"  - {lbl}: {val}" for lbl, val in zip(labels, props)]
        elif file_type == "DXF":
            labels = ["Entidades", "Ext. Mínima", "Ext. Máxima"]
            lines = [f"  - {lbl}: {val}" for lbl, val in zip(labels, props)]
        elif file_type == "PDF":
            labels = ["Páginas", "Autor", "Criador", "Hash do Conteúdo"]
            formatted_props = [
                props[0],
                props[1],
                props[2],
                f"{props[3][:12]}...",
            ]
            lines = [f"  - {lbl}: {val}" for lbl, val in zip(labels, formatted_props)]
        elif file_type == "DWG":
            lines = [f"  - Hash SHA256: {props[0][:24]}..."]

        return header + "\n".join(lines)

    def _update_row_status(self, table, row, props, status_msg, are_equal):
        """Atualiza a cor e a tooltip de uma linha com base no resultado."""
        status_item = table.item(row, 2)
        file_item = table.item(row, 1)
        if not file_item or not status_item:
            return

        file_type = self.cmb_file_type.currentText()
        tooltip = f"Caminho: {file_item.data(Qt.ItemDataRole.UserRole)}"
        tooltip += self._format_properties_tooltip(props, file_type)

        if status_msg != "OK":
            status_text, color = "⚠️", QColor("#FFC107")
            tooltip += f"\nStatus: {status_msg}"
        elif are_equal:
            status_text, color = "✓", QColor("#4CAF50")
            status_item.setToolTip("Arquivos equivalentes")
        elif are_equal is False:
            status_text, color = "X", QColor("#F44336")
            status_item.setToolTip("Arquivos diferentes")
        else:
            status_text, color = "", QColor("gray")
            status_item.setToolTip("Sem par para comparação")

        status_item.setText(status_text)
        file_item.setToolTip(tooltip)
        for col in range(table.columnCount()):
            if item := table.item(row, col):
                item.setForeground(color)

    def _clear_all(self):
        """Limpa todos os arquivos de ambas as tabelas e reseta a barra de progresso."""
        if self.table_a_widget:
            self.table_a_widget.setRowCount(0)
        if self.table_b_widget:
            self.table_b_widget.setRowCount(0)
        if self.progress_bar:
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(False)


class FormManager:
    """Gerencia a instância do formulário para garantir que seja um singleton."""

    _instance = None

    @classmethod
    def _reset_instance(cls):
        """Limpa a referência à instância quando o formulário é fechado."""
        cls._instance = None
        if hasattr(g, "COMPARAR_FORM"):
            g.COMPARAR_FORM = None

    @classmethod
    def show_form(cls, parent=None):
        """Cria e exibe o formulário, garantindo uma única instância visível."""
        if cls._instance is None:
            cls._instance = FormCompararArquivos(parent)
            g.COMPARAR_FORM = cls._instance
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
    try:
        main()
    except (ImportError, RuntimeError, IOError) as e:
        logging.critical("ERRO NÃO TRATADO:", exc_info=True)
        MENSAGEM_ERRO = (
            f"Não foi possível iniciar o aplicativo: {e}.\n"
            "Verifique as dependências e execute a partir do entrypoint principal."
        )
        show_error("Erro Crítico", MENSAGEM_ERRO)
        sys.exit(1)
    sys.exit(app.exec())
