"""
Widget de gerenciamento de avisos para a interface administrativa.
Permite listar, adicionar, editar e excluir avisos do sistema.
"""

import logging

from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDialogButtonBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.exc import SQLAlchemyError

from src.models.models import Aviso
from src.utils import ipc_manager
from src.utils.banco_dados import get_session
from src.utils.estilo import aplicar_estilo_botao, aplicar_estilo_table_widget
from src.utils.themed_widgets import ThemedDialog
from src.utils.utilitarios import aplicar_medida_borda_espaco, ask_yes_no, show_error


class AvisosWidget(QWidget):
    """Widget para a aba de Gerenciamento de Avisos."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.table_avisos = QTableWidget()
        self._setup_ui()
        self._load_avisos()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        aplicar_medida_borda_espaco(main_layout, 10)

        # Tabela
        self.table_avisos.setColumnCount(4)
        self.table_avisos.setHorizontalHeaderLabels(["ID", "Ordem", "Texto", "Ativo"])
        header = self.table_avisos.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        # Ocultar coluna ID
        self.table_avisos.hideColumn(0)

        aplicar_estilo_table_widget(self.table_avisos)
        self.table_avisos.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table_avisos.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table_avisos.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_avisos.verticalHeader().setVisible(False)
        self.table_avisos.setAlternatingRowColors(True)

        main_layout.addWidget(self.table_avisos)

        # Botões
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        add_btn = QPushButton("➕ Adicionar")
        add_btn.setToolTip("Adicionar novo aviso (Ctrl+N)")
        add_btn.setShortcut(QKeySequence("Ctrl+N"))
        add_btn.setSizePolicy(QSizePolicy.Policy.Expanding,
                              QSizePolicy.Policy.Preferred)
        aplicar_estilo_botao(add_btn, "verde")
        add_btn.clicked.connect(self._add_aviso)

        edit_btn = QPushButton("✏️ Editar")
        edit_btn.setToolTip("Editar aviso selecionado (F2)")
        edit_btn.setShortcut(QKeySequence("F2"))
        edit_btn.setSizePolicy(QSizePolicy.Policy.Expanding,
                               QSizePolicy.Policy.Preferred)
        aplicar_estilo_botao(edit_btn, "azul")
        edit_btn.clicked.connect(self._edit_aviso)

        del_btn = QPushButton("🗑️ Excluir")
        del_btn.setToolTip("Excluir aviso selecionado (Delete)")
        del_btn.setShortcut(QKeySequence("Delete"))
        del_btn.setSizePolicy(QSizePolicy.Policy.Expanding,
                              QSizePolicy.Policy.Preferred)
        aplicar_estilo_botao(del_btn, "vermelho")
        del_btn.clicked.connect(self._delete_aviso)

        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(del_btn)

        main_layout.addLayout(btn_layout)

    def _load_avisos(self):
        try:
            self.table_avisos.setRowCount(0)
            with get_session() as session:
                avisos = session.query(Aviso).order_by(Aviso.ordem).all()
                self.table_avisos.setRowCount(len(avisos))
                for i, aviso in enumerate(avisos):
                    self.table_avisos.setItem(i, 0, QTableWidgetItem(str(aviso.id)))

                    self.table_avisos.setItem(i, 1, QTableWidgetItem(str(aviso.ordem)))

                    # Texto (pode ser HTML, mostramos plain text ou curto)
                    texto_item = QTableWidgetItem(aviso.texto)
                    texto_item.setToolTip(aviso.texto)
                    self.table_avisos.setItem(i, 2, texto_item)

                    ativo_item = QTableWidgetItem("Sim" if aviso.ativo else "Não")
                    self.table_avisos.setItem(i, 3, ativo_item)
        except SQLAlchemyError as e:
            logging.error("Erro ao carregar avisos: %s", e)
            show_error("Erro", "Falha ao carregar avisos.", self)

    def _add_aviso(self):
        self._show_editor_dialog()

    def _edit_aviso(self):
        row = self.table_avisos.currentRow()
        if row < 0:
            return
        aviso_id = int(self.table_avisos.item(row, 0).text())
        self._show_editor_dialog(aviso_id)

    def _delete_aviso(self):
        row = self.table_avisos.currentRow()
        if row < 0:
            return
        aviso_id = int(self.table_avisos.item(row, 0).text())

        if not ask_yes_no("Confirmar", "Tem certeza que deseja excluir este aviso?"):
            return

        try:
            with get_session() as session:
                aviso = session.query(Aviso).get(aviso_id)
                if aviso:
                    session.delete(aviso)
                # Commit é automático pelo context manager se não houver erro
            # Reordenar automaticamente após exclusão
            self._reorder_avisos()
            ipc_manager.send_update_signal(ipc_manager.AVISOS_SIGNAL_FILE)
            self._load_avisos()
        except SQLAlchemyError as e:
            logging.error("Erro ao excluir aviso: %s", e)
            show_error("Erro", "Falha ao excluir aviso.", self)

    def _reorder_avisos(self):
        """Reordena todos os avisos sequencialmente baseado na ordem atual."""
        try:
            with get_session() as session:
                avisos = session.query(Aviso).order_by(Aviso.ordem).all()
                for i, aviso in enumerate(avisos, start=1):
                    aviso.ordem = i
        except SQLAlchemyError as e:
            logging.error("Erro ao reordenar avisos: %s", e)

    # pylint: disable=too-many-statements, too-many-locals

    def _show_editor_dialog(self, aviso_id=None):
        dialog = ThemedDialog(self)
        dialog.setWindowTitle("Editar Aviso" if aviso_id else "Novo Aviso")
        dialog.setMinimumWidth(400)

        main_layout = QVBoxLayout(dialog)
        aplicar_medida_borda_espaco(main_layout, 10, 5)

        # Campo de texto
        texto_label = QLabel("Texto (HTML permitido, auto-numerado):")
        texto_edit = QTextEdit()
        main_layout.addWidget(texto_label)
        main_layout.addWidget(texto_edit)

        # Widgets para ordem e ativo
        ordem_spin = QSpinBox()
        ordem_spin.setRange(0, 9999)
        ativo_chk = QCheckBox("Ativo")
        ativo_chk.setChecked(True)

        # Para novo aviso, definir ordem automaticamente como o próximo disponível
        if aviso_id is None:
            try:
                with get_session() as session:
                    max_ordem_result = session.query(
                        Aviso.ordem).filter_by(ativo=True).all()
                    if max_ordem_result:
                        proxima_ordem = max(a[0] for a in max_ordem_result) + 1
                    else:
                        proxima_ordem = 1
                    ordem_spin.setValue(proxima_ordem)
            except SQLAlchemyError:
                ordem_spin.setValue(1)  # fallback

        if aviso_id:
            with get_session() as session:
                aviso = session.query(Aviso).get(aviso_id)
                if aviso:
                    # Usar setPlainText para editar o código HTML cru.
                    texto_edit.setPlainText(aviso.texto)
                    ativo_chk.setChecked(aviso.ativo)
                    ordem_spin.setValue(aviso.ordem)

        # Layout inferior com ordem, checkbox ativo e botões
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)

        ordem_label = QLabel("Ordem:")

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        bottom_layout.addWidget(ordem_label)
        bottom_layout.addWidget(ordem_spin)
        bottom_layout.addWidget(ativo_chk)
        bottom_layout.addStretch()  # Para empurrar os botões para a direita
        bottom_layout.addWidget(buttons)

        main_layout.addLayout(bottom_layout)

        if dialog.exec():
            novo_texto = texto_edit.toPlainText()
            novo_ativo = ativo_chk.isChecked()
            nova_ordem = ordem_spin.value()

            try:
                with get_session() as session:
                    if aviso_id:
                        aviso = session.query(Aviso).get(aviso_id)
                        if aviso:
                            aviso.texto = novo_texto
                            aviso.ativo = novo_ativo
                            aviso.ordem = nova_ordem
                    else:
                        novo_aviso = Aviso(
                            texto=novo_texto, ativo=novo_ativo, ordem=nova_ordem
                        )
                        session.add(novo_aviso)
                # Reordenar automaticamente após qualquer alteração
                self._reorder_avisos()
                ipc_manager.send_update_signal(ipc_manager.AVISOS_SIGNAL_FILE)
                self._load_avisos()
            except SQLAlchemyError as e:
                logging.error("Erro ao salvar aviso: %s", e)
                show_error("Erro", "Falha ao salvar aviso.", self)
