"""
Módulo para o formulário de Comparador Geométrico de Ficheiros STEP.

Este formulário permite aos utilizadores carregar ficheiros STEP (.step, .stp) em
duas listas lado a lado e realizar uma comparação geométrica detalhada.
A comparação utiliza a biblioteca python-occ-core para extrair e comparar
propriedades como topologia, volume, área de superfície, centro de massa e
momentos de inércia.
"""

import hashlib
import os
import sys
from typing import Optional

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
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
from src.utils.estilo import aplicar_estilo_botao, obter_tema_atual
from src.utils.janelas import Janela
from src.utils.utilitarios import (
    ICON_PATH,
    aplicar_medida_borda_espaco,
    show_error,
    show_warning,
)

# Tenta importar as bibliotecas da python-occ
try:
    from OCC.Core.BRepGProp import brepgprop
    from OCC.Core.GProp import GProp_GProps
    from OCC.Core.STEPControl import STEPControl_Reader
    from OCC.Core.TopAbs import TopAbs_EDGE, TopAbs_FACE, TopAbs_VERTEX
    from OCC.Core.TopExp import TopExp_Explorer

    PYTHON_OCC_AVAILABLE = True
except ImportError:
    PYTHON_OCC_AVAILABLE = False

# --- Constantes de Configuração ---
LARGURA_FORM = 500
ALTURA_FORM = 513
MARGEM_LAYOUT = 10


class FileTableWidget(QTableWidget):
    """
    Tabela personalizada que aceita ficheiros arrastados e soltos,
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

        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["#", "Ficheiro", "Status"])
        self.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Interactive
        )
        self.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Interactive
        )
        self.setColumnWidth(0, 20)
        self.setColumnWidth(2, 60)
        self.verticalHeader().setVisible(False)

        self.other_table = None

    def set_other_table(self, other_table_widget):
        """Define uma referência à outra tabela para verificação de duplicados."""
        self.other_table = other_table_widget

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
        """Aceita o evento de arrastar se os dados contiverem ficheiros."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
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
        """Processa os ficheiros soltos, filtrando por .step e .stp."""
        files_to_add = [
            url.toLocalFile()
            for url in event.mimeData().urls()
            if url.isLocalFile()
            and url.toLocalFile().lower().endswith((".step", ".stp"))
        ]
        if files_to_add:
            self.add_files(files_to_add)

    def add_files(self, file_paths):
        """Adiciona uma lista de caminhos de ficheiro à tabela, evitando duplicados."""
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
                "Ficheiros Ignorados",
                f"{skipped_count} ficheiro(s) não foram adicionados porque já existem.",
                parent=self.window(),
            )


class FormCompararArquivos(QDialog):
    """Formulário para Comparação Geométrica de Ficheiros STEP."""

    def __init__(self, parent=None):
        """Inicializa o formulário."""
        super().__init__(parent)
        self.table_a_widget: Optional[FileTableWidget] = None
        self.table_b_widget: Optional[FileTableWidget] = None
        self.progress_bar: Optional[QProgressBar] = None
        self.btn_compare: Optional[QPushButton] = None
        self.btn_clear: Optional[QPushButton] = None
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
        barra.titulo.setText("Comparador Geométrico de Ficheiros STEP")
        vlayout.addWidget(barra)

        conteudo = QWidget()
        layout_principal = QVBoxLayout(conteudo)
        aplicar_medida_borda_espaco(layout_principal, MARGEM_LAYOUT)
        vlayout.addWidget(conteudo)

        if not PYTHON_OCC_AVAILABLE:
            show_error(
                "Biblioteca Faltando",
                "A biblioteca 'python-occ-core' não foi encontrada.\n\n"
                "Instale-a com: 'conda install -c conda-forge python-occ-core'",
                parent=self,
            )
            QApplication.instance().callLater(self.close)
            return

        self._setup_layouts(layout_principal)

    def _setup_layouts(self, main_layout: QVBoxLayout):
        """Configura os layouts internos do formulário."""
        lists_layout = QHBoxLayout()

        list_a_gb = QGroupBox("Lista A")
        list_a_layout = QVBoxLayout(list_a_gb)
        self.table_a_widget = FileTableWidget()
        btn_add_a = QPushButton("➕ Adicionar à Lista A")
        btn_add_a.clicked.connect(lambda: self._select_files(self.table_a_widget))
        aplicar_estilo_botao(btn_add_a, "cinza")
        list_a_layout.addWidget(btn_add_a)
        list_a_layout.addWidget(self.table_a_widget)
        aplicar_medida_borda_espaco(list_a_layout, 5)

        list_b_gb = QGroupBox("Lista B")
        list_b_layout = QVBoxLayout(list_b_gb)
        self.table_b_widget = FileTableWidget()
        btn_add_b = QPushButton("➕ Adicionar à Lista B")
        btn_add_b.clicked.connect(lambda: self._select_files(self.table_b_widget))
        aplicar_estilo_botao(btn_add_b, "cinza")
        list_b_layout.addWidget(btn_add_b)
        list_b_layout.addWidget(self.table_b_widget)
        aplicar_medida_borda_espaco(list_b_layout, 5)

        self.table_a_widget.set_other_table(self.table_b_widget)
        self.table_b_widget.set_other_table(self.table_a_widget)

        lists_layout.addWidget(list_a_gb)
        lists_layout.addWidget(list_b_gb)

        action_layout = QHBoxLayout()
        self.btn_compare = QPushButton("🔄 Comparar Geometrias")
        self.btn_compare.clicked.connect(self._compare_files)
        aplicar_estilo_botao(self.btn_compare, "verde")
        self.btn_clear = QPushButton("🧹 Limpar Tudo")
        self.btn_clear.clicked.connect(self._clear_all)
        aplicar_estilo_botao(self.btn_clear, "vermelho")
        action_layout.addWidget(self.btn_compare)
        action_layout.addWidget(self.btn_clear)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setToolTip("Progresso da comparação")

        main_layout.addLayout(lists_layout)
        main_layout.addLayout(action_layout)
        main_layout.addWidget(self.progress_bar)

    def _select_files(self, table_widget):
        """Abre uma caixa de diálogo para selecionar ficheiros STEP."""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Selecionar Ficheiros STEP",
            "",
            "STEP Files (*.step *.stp);;All Files (*)",
        )
        if file_paths:
            table_widget.add_files(file_paths)

    def _get_file_hash(self, file_path):
        """Calcula o hash SHA256 da secção de dados de um ficheiro."""
        sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            data_start_pos = content.find(b"DATA;")
            if data_start_pos != -1:
                sha256.update(content[data_start_pos:])
            else:
                sha256.update(content)
            return sha256.hexdigest()
        except IOError:
            return None

    def _get_geometric_properties(self, file_path):
        """Lê um ficheiro STEP e extrai um conjunto de propriedades geométricas."""
        try:
            reader = STEPControl_Reader()
            if reader.ReadFile(file_path) != 1:
                return None, "Erro ao ler o ficheiro"
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
            principal_props = props_vol.PrincipalProperties()
            i1, i2, i3 = principal_props.Moments()

            props_surf = GProp_GProps()
            brepgprop.SurfaceProperties(shape, props_surf)

            return (
                num_faces,
                num_edges,
                num_vertices,
                round(props_vol.Mass(), 6),
                round(props_surf.Mass(), 6),
                round(com.X(), 6),
                round(com.Y(), 6),
                round(com.Z(), 6),
                round(i1, 6),
                round(i2, 6),
                round(i3, 6),
            ), "OK"
        except (IOError, RuntimeError) as e:
            return None, f"Exceção: {str(e)}"

    def _compare_files(self):
        """Inicia o processo de comparação para todos os ficheiros nas listas."""
        if self.table_a_widget.rowCount() == 0 or self.table_b_widget.rowCount() == 0:
            show_warning("Aviso", "Adicione ficheiros em ambas as listas.", parent=self)
            return

        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.btn_compare.setEnabled(False)
        self.btn_clear.setEnabled(False)

        try:
            count_a = self.table_a_widget.rowCount()
            count_b = self.table_b_widget.rowCount()
            max_count = max(count_a, count_b)

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
                            self.table_a_widget, i, None, "OK", True, True
                        )
                        self._update_row_status(
                            self.table_b_widget, i, None, "OK", True, True
                        )
                        continue

                props_a, status_a = (
                    self._get_geometric_properties(path_a)
                    if path_a
                    else (None, "Sem par")
                )
                props_b, status_b = (
                    self._get_geometric_properties(path_b)
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

    def _update_row_status(
        self, table, row, props, status_msg, are_equal, hash_match=False
    ):
        """Atualiza a cor e a tooltip de uma linha com base no resultado."""
        status_item = table.item(row, 2)
        file_item = table.item(row, 1)
        if not file_item or not status_item:
            return

        file_path = file_item.data(Qt.ItemDataRole.UserRole)
        tooltip = f"Caminho: {file_path}"
        properties_text = ""
        if props:
            properties_text = (
                f"\n\nPropriedades Geométricas:\n"
                f"  - Topologia: {props[0]} Faces, {props[1]} Arestas, {props[2]} Vértices\n"
                f"  - Volume: {props[3]}\n  - Área de Superfície: {props[4]}\n"
                f"  - Centro de Massa: ({props[5]}, {props[6]}, {props[7]})\n"
                f"  - Mom. Inércia: ({props[8]}, {props[9]}, {props[10]})"
            )

        if hash_match:
            status_text, color = "✓", QColor("#17A2B8")
            tooltip += "\n\nDados idênticos (correspondência de hash da secção DATA)."
        elif status_msg != "OK":
            status_text, color = "⚠️", QColor("#FFC107")
            tooltip += f"\nStatus: {status_msg}"
        elif are_equal:
            status_text, color = "✓", QColor("#4CAF50")
            tooltip += properties_text
        elif are_equal is False:
            status_text, color = "X", QColor("#F44336")
            tooltip += properties_text
        else:
            status_text, color = "", QColor("white")
            tooltip += "\n\nSem par para comparação"

        status_item.setText(status_text)
        file_item.setToolTip(tooltip)
        for col in range(table.columnCount()):
            if item := table.item(row, col):
                item.setForeground(color)

    def _clear_all(self):
        """Limpa todos os ficheiros de ambas as tabelas."""
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
    except (ImportError, NameError) as e:
        show_error(
            "Erro de Dependência",
            f"Não foi possível iniciar o aplicativo: {e}.\n"
            "Execute este formulário a partir do aplicativo principal.",
        )
        sys.exit(1)
    sys.exit(app.exec())
