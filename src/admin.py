"""
Módulo de Administração Centralizado.

Este módulo fornece uma interface gráfica unificada para administradores
gerenciarem a aplicação, combinando as funcionalidades de:
- Gerenciamento de instâncias ativas (visualização e encerramento forçado).
- Atualização da aplicação (seleção manual de arquivo e instalação).
- Gerenciamento de usuários (redefinir senhas, alterar permissões e excluir).

O acesso à ferramenta requer autenticação de administrador.
"""

# pylint: disable=R0902

import logging
import os
import sys
import time
from datetime import datetime

from PySide6.QtCore import QEvent, QObject, QSettings, Qt, QTimer
from PySide6.QtGui import QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.exc import SQLAlchemyError

from src.config import globals as g
from src.forms import form_aut
from src.models.models import Usuario
from src.utils.banco_dados import get_session
from src.utils.controlador import buscar_debounced
from src.utils.estilo import (
    aplicar_estilo_botao,
    aplicar_estilo_table_widget,
)
from src.utils.interface_manager import safe_process_events
from src.utils.session_manager import (
    force_shutdown_all_instances,
    obter_sessoes_ativas,
)
from src.utils.theme_manager import theme_manager
from src.utils.update_manager import get_installed_version, run_update_process
from src.utils.usuarios import (
    RESET_PASSWORD_HASH,
    alternar_permissao_editor,
    excluir_usuario,
    resetar_senha,
)
from src.utils.utilitarios import (
    ICON_PATH,
    aplicar_medida_borda_espaco,
    ask_yes_no,
    setup_logging,
    show_error,
    show_info,
)

ADMIN_INACTIVITY_TIMEOUT_MS = 10 * 60 * 1000

_INACTIVITY_EVENTS = {
    QEvent.Type.MouseButtonPress,
    QEvent.Type.MouseButtonRelease,
    QEvent.Type.MouseMove,
    QEvent.Type.KeyPress,
    QEvent.Type.KeyRelease,
    QEvent.Type.Wheel,
    QEvent.Type.FocusIn,
}


class _InactivityEventFilter(QObject):
    """Reinicia o timer quando eventos de interação são detectados."""

    def __init__(self, on_activity):
        super().__init__()
        self._on_activity = on_activity

    def eventFilter(  # pylint: disable=invalid-name
        self, obj, event
    ):  # pylint: disable=unused-argument
        """Intercepta eventos de UI para reiniciar o timer de inatividade."""
        if event.type() in _INACTIVITY_EVENTS:
            self._on_activity()
        return super().eventFilter(obj, event)


def obter_dir_base_local():
    """Determina o diretório base para importações corretas."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = obter_dir_base_local()
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


class InstancesWidget(QWidget):
    """Widget para a aba de Gerenciamento de Instâncias."""

    def __init__(self, parent=None):
        """Inicializa o widget de gerenciamento de instâncias."""
        super().__init__(parent)
        self.table_sessoes = QTableWidget()
        self.label_total_instancias = QLabel("0")
        self.label_ultima_atualizacao = QLabel("N/A")
        self.status_label = QLabel()
        self.timer_atualizacao = QTimer(self)
        self._setup_ui()
        self._initialize_data()

    def _setup_ui(self):
        """Configura a interface do usuário para o widget."""
        main_layout = QVBoxLayout(self)
        aplicar_medida_borda_espaco(main_layout, 10, 10)

        frame_info = self._create_info_frame()
        main_layout.addWidget(frame_info)

        self.table_sessoes.setColumnCount(3)
        self.table_sessoes.setHorizontalHeaderLabels(
            ["ID Sessão", "Hostname", "Última Atividade"]
        )
        header = self.table_sessoes.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table_sessoes.setColumnWidth(0, 80)
        self.table_sessoes.setToolTip("Lista de instâncias ativas da aplicação")
        aplicar_estilo_table_widget(self.table_sessoes)
        self.table_sessoes.setSortingEnabled(True)
        self.table_sessoes.setAlternatingRowColors(True)
        self.table_sessoes.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table_sessoes.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table_sessoes.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_sessoes.verticalHeader().setVisible(False)

        main_layout.addWidget(self.table_sessoes)

        action_buttons = self._create_action_buttons()
        main_layout.addWidget(action_buttons)

        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #0078d4; margin-top: 5px;")
        self.status_label.setVisible(False)
        main_layout.addWidget(self.status_label)

        self._setup_keyboard_shortcuts()

    def _setup_keyboard_shortcuts(self):
        """Configura atalhos de teclado para o widget de instâncias."""
        refresh_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        refresh_shortcut.activated.connect(self._load_sessions)

    def _create_info_frame(self):
        """Cria o frame de informações do sistema."""
        frame = QGroupBox("Informações do Sistema")
        layout = QGridLayout(frame)
        aplicar_medida_borda_espaco(layout)
        layout.addWidget(QLabel("Total de Instâncias Ativas:"), 0, 0)
        self.label_total_instancias.setStyleSheet("font-weight: bold; color: #0078d4;")
        layout.addWidget(self.label_total_instancias, 0, 1)
        layout.addWidget(QLabel("Última Atualização:"), 1, 0)
        layout.addWidget(self.label_ultima_atualizacao, 1, 1)
        return frame

    def _create_action_buttons(self):
        """Cria o container com os botões de ação."""
        container = QWidget()
        buttons_layout = QHBoxLayout(container)
        aplicar_medida_borda_espaco(buttons_layout, 0)
        buttons_layout.setSpacing(10)

        atualizar_btn = QPushButton("🔄 Atualizar")
        atualizar_btn.setToolTip("Atualizar lista de instâncias ativas (F5)")
        atualizar_btn.setShortcut(QKeySequence("F5"))
        aplicar_estilo_botao(atualizar_btn, "azul")
        atualizar_btn.clicked.connect(self._load_sessions)
        buttons_layout.addWidget(atualizar_btn)

        shutdown_btn = QPushButton("⚠️ Shutdown Geral")
        shutdown_btn.setToolTip("Encerrar todas as instâncias ativas (Ctrl+Shift+Q)")
        shutdown_btn.setShortcut(QKeySequence("Ctrl+Shift+Q"))
        aplicar_estilo_botao(shutdown_btn, "vermelho")
        shutdown_btn.clicked.connect(self._start_global_shutdown)
        buttons_layout.addWidget(shutdown_btn)

        return container

    def _initialize_data(self):
        """Inicializa os dados e o timer de atualização."""
        self._load_sessions()
        self.timer_atualizacao.timeout.connect(self._load_sessions)
        self.timer_atualizacao.start(10000)

    def _load_sessions(self):
        """Carrega e exibe as sessões ativas."""
        try:
            self.table_sessoes.setRowCount(0)
            sessoes = obter_sessoes_ativas()
            self.label_total_instancias.setText(str(len(sessoes)))
            self.label_ultima_atualizacao.setText(datetime.now().strftime("%H:%M:%S"))
            for sessao in sessoes:
                row_position = self.table_sessoes.rowCount()
                self.table_sessoes.insertRow(row_position)
                self.table_sessoes.setItem(
                    row_position,
                    0,
                    QTableWidgetItem(sessao.get("session_id", "N/A")[:8]),
                )
                self.table_sessoes.setItem(
                    row_position, 1, QTableWidgetItem(sessao.get("hostname", "N/A"))
                )
                self.table_sessoes.setItem(
                    row_position, 2, QTableWidgetItem(sessao.get("last_updated", "N/A"))
                )
            self.table_sessoes.setCurrentCell(-1, -1)
        except (KeyError, AttributeError, TypeError) as e:
            logging.error("Erro ao carregar sessões: %s", e)
            self._set_status_message("Erro ao carregar sessões.")

    def _update_shutdown_status(self, active_sessions: int):
        """Atualiza a mensagem de status durante o shutdown."""
        self._set_status_message(f"Aguardando {active_sessions} instância(s) fechar...")

    def _start_global_shutdown(self):
        """Inicia o processo de encerramento de todas as instâncias."""
        msg = "Todas as instâncias da aplicação serão fechadas. Deseja continuar?"
        if not ask_yes_no("Confirmar Shutdown", msg, parent=self):
            return
        self._set_status_message("Enviando comando de encerramento...")
        safe_process_events()

        success = False
        try:
            success = force_shutdown_all_instances(self._update_shutdown_status)
        except (RuntimeError, ConnectionError, TimeoutError) as e:
            logging.error("Erro no shutdown: %s", e)
            show_error(
                "Erro no Encerramento",
                f"Não foi possível executar o encerramento: {e}",
                parent=self,
            )

        if success:
            show_info(
                "Sucesso",
                "Todas as instâncias foram encerradas com sucesso.",
                parent=self,
            )
            self._set_status_message("Encerramento concluído com sucesso.")
        else:
            show_error("Timeout", "As instâncias não fecharam a tempo.", parent=self)
            self._set_status_message("Falha no encerramento (timeout).")

        self._load_sessions()
        QTimer.singleShot(5000, lambda: self._set_status_message(""))

    def _set_status_message(self, message: str):
        """Define a mensagem de status e controla a visibilidade do label."""
        if message:
            self.status_label.setText(message)
            self.status_label.setVisible(True)
        else:
            self.status_label.setVisible(False)

    def stop_timer(self):
        """Para o timer de atualização."""
        self.timer_atualizacao.stop()


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
        try:
            run_update_process(self.selected_file_path, self._update_progress_ui)
            self._update_progress_ui("Concluído!", 100)
            time.sleep(2)
            self._reset_widget_state()
        except (ValueError, ConnectionError, RuntimeError, IOError) as e:
            logging.error("Erro no processo de atualização: %s", e)
            show_error("Erro de Atualização", f"Ocorreu um erro: {e}", parent=self)
            self._reset_widget_state()
        finally:
            QApplication.restoreOverrideCursor()


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
        g.LIST_USUARIO.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
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


class AdminTool(QMainWindow):
    """Janela principal da Ferramenta Administrativa."""

    def __init__(self):
        """Inicializa a janela principal."""
        super().__init__()
        self.setWindowTitle("Ferramenta Administrativa")
        if ICON_PATH and os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))

        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowMaximizeButtonHint
            | Qt.WindowCloseButtonHint
        )
        self._restore_window_state()
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        aplicar_medida_borda_espaco(main_layout, 0, 0)
        self.main_tool_widget = QWidget()
        main_layout.addWidget(self.main_tool_widget)
        self.instances_tab = InstancesWidget()
        self.updater_tab = UpdaterWidget()
        self.user_management_tab = UserManagementWidget()
        self._setup_main_tool_ui()
        self._setup_global_shortcuts()
        self._autenticado = False
        self._setup_inactivity_timer()
        QTimer.singleShot(0, self._solicitar_autenticacao_admin)

    def _setup_main_tool_ui(self):
        """Configura a UI principal da ferramenta com abas."""
        layout = QVBoxLayout(self.main_tool_widget)
        aplicar_medida_borda_espaco(layout, 0, 0)
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("QTabWidget::pane { border: 0; }")
        self.tab_widget.addTab(self.instances_tab, "🔧 Gerenciar Instâncias")
        self.tab_widget.addTab(self.user_management_tab, "👥 Gerenciar Usuários")
        self.tab_widget.addTab(self.updater_tab, "🔄 Atualizador")

        self.tab_widget.setTabToolTip(
            0, "Gerenciar instâncias ativas da aplicação (Ctrl+1)"
        )
        self.tab_widget.setTabToolTip(1, "Gerenciar usuários do sistema (Ctrl+2)")
        self.tab_widget.setTabToolTip(2, "Atualizar a aplicação (Ctrl+3)")

        layout.addWidget(self.tab_widget)

    def _setup_global_shortcuts(self):
        """Configura atalhos globais da aplicação."""
        tab1_shortcut = QShortcut(QKeySequence("Ctrl+1"), self)
        tab1_shortcut.activated.connect(lambda: self.tab_widget.setCurrentIndex(0))

        tab2_shortcut = QShortcut(QKeySequence("Ctrl+2"), self)
        tab2_shortcut.activated.connect(lambda: self.tab_widget.setCurrentIndex(1))

        tab3_shortcut = QShortcut(QKeySequence("Ctrl+3"), self)
        tab3_shortcut.activated.connect(lambda: self.tab_widget.setCurrentIndex(2))

        close_shortcut = QShortcut(QKeySequence("Alt+F4"), self)
        close_shortcut.activated.connect(self.close)

    def _restore_window_state(self):
        """Restaura posição e tamanho salvos da janela administrativa."""
        settings = QSettings()
        geometry = settings.value("admin/geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.setMinimumSize(380, 400)
            self.resize(380, 400)

    def _save_window_state(self):
        """Persiste a geometria atual para reutilização futura."""
        settings = QSettings()
        settings.setValue("admin/geometry", self.saveGeometry())

    def _setup_inactivity_timer(self):
        self._inactivity_timer = QTimer(self)
        self._inactivity_timer.setInterval(ADMIN_INACTIVITY_TIMEOUT_MS)
        self._inactivity_timer.setSingleShot(True)
        self._inactivity_timer.timeout.connect(self._handle_inactivity_timeout)
        self._inactivity_filter = _InactivityEventFilter(self._reset_inactivity_timer)
        self._install_filter_recursively(self, self._inactivity_filter)
        self._reset_inactivity_timer()

    @staticmethod
    def _install_filter_recursively(widget, filtro):
        widget.installEventFilter(filtro)
        for child in widget.findChildren(QWidget):
            child.installEventFilter(filtro)

    def _reset_inactivity_timer(self):
        if hasattr(self, "_inactivity_timer"):
            self._inactivity_timer.start()

    def _handle_inactivity_timeout(self):
        logging.warning("Fechando ferramenta administrativa por inatividade.")
        self.close()

    def _solicitar_autenticacao_admin(self):
        """Abre o formulário compartilhado de autenticação para validar admins."""
        g.USUARIO_ID = None
        g.LOGIN = True
        parent = self if self.isVisible() else None
        logging.info("Abrindo formulário de login administrativo (parent=%s)", parent)
        form_aut.main(parent)
        dialog = g.AUTEN_FORM
        if dialog is None:
            show_error(
                "Erro",
                "Não foi possível abrir o formulário de autenticação.",
                parent=self,
            )
            self.close()
            return
        dialog.finished.connect(self._on_auth_dialog_closed)

    def _on_auth_dialog_closed(self, _result: int):  # pylint: disable=unused-argument
        """Processa o fechamento do formulário de autenticação."""
        dialog = g.AUTEN_FORM
        if dialog is not None:
            try:
                dialog.finished.disconnect(self._on_auth_dialog_closed)
            except (RuntimeError, TypeError):
                pass
        g.AUTEN_FORM = None
        g.LOGIN = None

        logging.info("Login administrativo finalizado. Usuario atual: %s", g.USUARIO_ID)
        if g.USUARIO_ID is None:
            self.close()
            return

        if not self._usuario_atual_e_admin():
            show_error(
                "Acesso Negado",
                "Apenas administradores podem usar esta ferramenta.",
                parent=self,
            )
            g.USUARIO_ID = None
            QTimer.singleShot(0, self._solicitar_autenticacao_admin)
            return

        self.show_main_tool()

    def _usuario_atual_e_admin(self) -> bool:
        """Confere se o usuário logado possui papel de administrador."""
        if g.USUARIO_ID is None:
            return False
        try:
            with get_session() as session:
                usuario_obj = session.get(Usuario, g.USUARIO_ID)
                logging.info(
                    "Verificando permissões do usuário %s (role=%s)",
                    g.USUARIO_ID,
                    getattr(usuario_obj, "role", None),
                )
                return bool(usuario_obj and usuario_obj.role == "admin")
        except SQLAlchemyError as e:
            logging.error("Erro ao verificar permissões administrativas: %s", e)
            show_error(
                "Erro",
                "Não foi possível validar as permissões do usuário.",
                parent=self,
            )
            return False

    def show_main_tool(self):
        """Mostra a ferramenta principal após a autenticação."""
        if self._autenticado:
            self._reset_inactivity_timer()
            return
        self._autenticado = True
        self._reset_inactivity_timer()
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):  # pylint: disable=C0103
        """Garante que o timer da aba de instâncias seja parado ao fechar."""
        self._save_window_state()
        if hasattr(self, "_inactivity_timer"):
            self._inactivity_timer.stop()
        self.instances_tab.stop_timer()
        event.accept()


def main():
    """Função principal para iniciar a aplicação."""
    setup_logging("admin.log", log_to_console=True)
    logging.info("Ferramenta Administrativa iniciada.")
    app = QApplication(sys.argv)
    app.setOrganizationName("raphadroid27")
    app.setApplicationName("Tabela-de-dobra")
    # Inicializa o tema salvo via ThemeManager
    try:
        theme_manager.initialize()
    except (AttributeError, RuntimeError):
        pass
    AdminTool()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
