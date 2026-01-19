"""
Widget de gerenciamento de usuários para a interface administrativa.
"""

import logging

from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.exc import SQLAlchemyError

from src.config import globals as g
from src.models.models import Usuario
from src.utils.banco_dados import get_session
from src.utils.controlador import buscar_debounced
from src.utils.estilo import (
    aplicar_estilo_botao,
    aplicar_estilo_table_widget,
)
from src.utils.usuarios import (
    RESET_PASSWORD_HASH,
    alternar_permissao_editor,
    excluir_usuario,
    resetar_senha,
)
from src.utils.utilitarios import (
    aplicar_medida_borda_espaco,
    show_error,
)


class UserManagementWidget(QWidget):
    """Widget para a aba de Gerenciamento de Usuários."""

    def __init__(self, parent=None):
        """Inicializa o widget de gerenciamento de usuários."""
        super().__init__(parent)
        self.usuario_busca_entry = QLineEdit()
        self.list_usuario = QTableWidget()
        self.toggle_role_btn = None
        self.resetar_senha_btn = None
        self.excluir_btn = None
        g.USUARIO_BUSCA_ENTRY = self.usuario_busca_entry
        g.LIST_USUARIO = self.list_usuario
        self._setup_ui()
        self._listar_usuarios()
        self.list_usuario.itemSelectionChanged.connect(self._update_buttons_state)
        self._update_buttons_state()
        self._setup_keyboard_shortcuts()

    def _setup_keyboard_shortcuts(self):
        """Configura atalhos de teclado para o widget de usuários."""
        focus_search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        focus_search_shortcut.activated.connect(self.usuario_busca_entry.setFocus)

    def _setup_ui(self):
        """Configura a interface do usuário para o widget."""
        main_layout = QVBoxLayout(self)
        aplicar_medida_borda_espaco(main_layout, 10, 10)
        self._create_search_frame(main_layout)
        self._create_table_widget(main_layout)
        self._create_action_buttons(main_layout)

    def _listar_usuarios(self):
        """Busca os usuários no banco de dados e atualiza a lista na interface."""
        try:
            with get_session() as session:
                self.list_usuario.setRowCount(0)
                usuarios = session.query(Usuario).order_by(Usuario.nome).all()
                for usuario in usuarios:
                    row_position = self.list_usuario.rowCount()
                    self.list_usuario.insertRow(row_position)
                    self.list_usuario.setItem(
                        row_position, 0, QTableWidgetItem(str(usuario.id))
                    )
                    self.list_usuario.setItem(
                        row_position, 1, QTableWidgetItem(usuario.nome)
                    )
                    self.list_usuario.setItem(
                        row_position, 2, QTableWidgetItem(usuario.role)
                    )
                    senha_resetada = (
                        "Sim" if usuario.senha == RESET_PASSWORD_HASH else "Não"
                    )
                    self.list_usuario.setItem(
                        row_position, 3, QTableWidgetItem(senha_resetada)
                    )
                self.list_usuario.setCurrentCell(-1, -1)
                self._update_buttons_state()
        except SQLAlchemyError as e:
            logging.error("Erro ao listar usuários: %s", e)
            show_error(
                "Erro de Banco de Dados",
                "Não foi possível carregar a lista de usuários.",
                parent=self,
            )

    def _create_search_frame(self, main_layout):
        """Cria o frame de busca de usuários."""
        frame_busca = QGroupBox("Filtrar Usuários")
        busca_layout = QGridLayout(frame_busca)
        aplicar_medida_borda_espaco(busca_layout)
        busca_layout.addWidget(QLabel("Usuário:"), 0, 0)
        self.usuario_busca_entry.setToolTip(
            "Digite parte do nome do usuário para buscar"
        )
        self.usuario_busca_entry.textChanged.connect(
            lambda: buscar_debounced("usuario")
        )
        busca_layout.addWidget(self.usuario_busca_entry, 0, 1)
        limpar_btn = QPushButton("🧹 Limpar")
        limpar_btn.setToolTip("Limpar filtro e mostrar todos os usuários (Ctrl+L)")
        limpar_btn.setShortcut(QKeySequence("Ctrl+L"))
        aplicar_estilo_botao(limpar_btn, "amarelo")
        limpar_btn.clicked.connect(self._limpar_busca_action)
        busca_layout.addWidget(limpar_btn, 0, 2)
        atualizar_btn = QPushButton("🔄")
        atualizar_btn.setToolTip("Atualizar lista de usuários (F5)")
        atualizar_btn.setShortcut(QKeySequence("F5"))
        atualizar_btn.setFixedWidth(40)
        aplicar_estilo_botao(atualizar_btn, "azul")
        atualizar_btn.clicked.connect(self._listar_usuarios)
        busca_layout.addWidget(atualizar_btn, 0, 3)
        main_layout.addWidget(frame_busca)

    def _limpar_busca_action(self):
        """Limpa o campo de busca e recarrega a lista completa de usuários."""
        self.usuario_busca_entry.clear()
        self._listar_usuarios()

    def _create_table_widget(self, main_layout):
        """Cria o QTableWidget para listar usuários."""
        g.LIST_USUARIO.setColumnCount(4)
        g.LIST_USUARIO.setHorizontalHeaderLabels(
            ["Id", "Nome", "Permissões", "Senha Resetada"]
        )
        g.LIST_USUARIO.setColumnHidden(0, True)
        header = g.LIST_USUARIO.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        g.LIST_USUARIO.setColumnWidth(2, 80)
        g.LIST_USUARIO.setColumnWidth(3, 100)
        g.LIST_USUARIO.setToolTip("Lista de usuários cadastrados no sistema")
        aplicar_estilo_table_widget(g.LIST_USUARIO)
        g.LIST_USUARIO.setSortingEnabled(True)
        g.LIST_USUARIO.setAlternatingRowColors(True)
        g.LIST_USUARIO.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        g.LIST_USUARIO.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        g.LIST_USUARIO.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        g.LIST_USUARIO.verticalHeader().setVisible(False)
        main_layout.addWidget(g.LIST_USUARIO)

    def _create_action_buttons(self, main_layout):
        """Cria os botões de ação."""
        container = QWidget()
        buttons_layout = QHBoxLayout(container)
        aplicar_medida_borda_espaco(buttons_layout, 0)
        buttons_layout.setSpacing(10)
        self.toggle_role_btn = QPushButton("👤 Alterar Permissão")
        self.toggle_role_btn.setToolTip(
            "Alterar permissão do usuário selecionado (Ctrl+A)"
        )
        self.toggle_role_btn.setShortcut(QKeySequence("Ctrl+A"))
        aplicar_estilo_botao(self.toggle_role_btn, "verde")
        self.toggle_role_btn.clicked.connect(self._toggle_role_action)
        buttons_layout.addWidget(self.toggle_role_btn)
        self.resetar_senha_btn = QPushButton("🔄 Resetar Senha")
        self.resetar_senha_btn.setToolTip(
            "Resetar senha do usuário selecionado (Ctrl+R)"
        )
        self.resetar_senha_btn.setShortcut(QKeySequence("Ctrl+R"))
        aplicar_estilo_botao(self.resetar_senha_btn, "amarelo")
        self.resetar_senha_btn.clicked.connect(self._resetar_senha_action)
        buttons_layout.addWidget(self.resetar_senha_btn)
        self.excluir_btn = QPushButton("🗑️ Excluir")
        self.excluir_btn.setToolTip("Excluir usuário selecionado (Delete)")
        self.excluir_btn.setShortcut(QKeySequence("Delete"))
        aplicar_estilo_botao(self.excluir_btn, "vermelho")
        self.excluir_btn.clicked.connect(self._excluir_usuario_action)
        buttons_layout.addWidget(self.excluir_btn)
        main_layout.addWidget(container)

    def _update_buttons_state(self):
        """Atualiza o estado dos botões de ação com base no item selecionado."""
        selected_items = self.list_usuario.selectedItems()
        has_selection = bool(selected_items)
        self.resetar_senha_btn.setEnabled(has_selection)
        self.excluir_btn.setEnabled(has_selection)
        self.toggle_role_btn.setEnabled(has_selection)
        if not has_selection:
            self.toggle_role_btn.setText("👤 Alterar Permissão")
            return
        current_row = self.list_usuario.currentRow()
        role_item = self.list_usuario.item(current_row, 2)
        if not role_item:
            return
        role = role_item.text()
        if role == "admin":
            self.toggle_role_btn.setEnabled(False)
            self.excluir_btn.setEnabled(False)
            self.toggle_role_btn.setText("👤 Alterar Permissão")
        elif role == "editor":
            self.toggle_role_btn.setText("👤 Tornar Viewer")
        else:
            self.toggle_role_btn.setText("👤 Tornar Editor")

    def _resetar_senha_action(self):
        """Chama a função centralizada para resetar a senha e atualiza a lista."""
        if resetar_senha(parent=self):
            self._listar_usuarios()

    def _excluir_usuario_action(self):
        """Chama a função centralizada para excluir o usuário e atualiza a lista."""
        if excluir_usuario(parent=self):
            self._listar_usuarios()

    def _toggle_role_action(self):
        """Chama a função centralizada para alterar a permissão e atualiza a lista."""
        if alternar_permissao_editor(parent=self):
            self._listar_usuarios()
