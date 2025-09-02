"""
Módulo de Administração Centralizado.

Este módulo fornece uma interface gráfica unificada para administradores
gerenciarem a aplicação, combinando as funcionalidades de:
- Gerenciamento de instâncias ativas (visualização e encerramento forçado).
- Atualização da aplicação (seleção manual de arquivo e instalação).
- Gerenciamento de usuários (redefinir senhas, alterar permissões e excluir).

O acesso à ferramenta requer autenticação de administrador.
"""

import hashlib
import logging
import os
import sys
import time
from datetime import datetime

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.exc import SQLAlchemyError

from src.components.barra_titulo import BarraTitulo
from src.config import globals as g
from src.models.models import Usuario
from src.utils.banco_dados import get_session
from src.utils.controlador import buscar
from src.utils.estilo import (
    aplicar_estilo_botao,
    aplicar_estilo_widget_auto_ajustavel,
    aplicar_tema_inicial,
    obter_estilo_progress_bar,
    obter_tema_atual,
)
from src.utils.session_manager import (
    force_shutdown_all_instances,
    obter_sessoes_ativas,
)
from src.utils.update_manager import get_installed_version, run_update_process
from src.utils.usuarios import (
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


def obter_dir_base_local():
    """Determina o diretório base para importações corretas."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = obter_dir_base_local()
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


class AdminAuthWidget(QWidget):
    """Widget para autenticação de administrador."""

    login_successful = Signal()

    def __init__(self, parent=None):
        """Inicializa o widget de autenticação."""
        super().__init__(parent)
        self.usuario_entry = QLineEdit()
        self.senha_entry = QLineEdit()
        self._setup_ui()
        self.usuario_entry.setFocus()

    def _setup_ui(self):
        """Configura a interface do usuário para o widget de autenticação."""
        main_layout = QVBoxLayout(self)
        aplicar_medida_borda_espaco(main_layout, 10)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel("Autenticação de Administrador")
        title_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; margin-bottom: 5px;"
        )
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        grid_layout = QGridLayout()
        grid_layout.setVerticalSpacing(10)
        grid_layout.setHorizontalSpacing(10)
        grid_layout.addWidget(QLabel("Usuário:"), 0, 0)
        self.usuario_entry.setPlaceholderText("Digite o usuário")
        aplicar_estilo_widget_auto_ajustavel(self.usuario_entry, "lineedit")
        grid_layout.addWidget(self.usuario_entry, 0, 1)

        grid_layout.addWidget(QLabel("Senha:"), 1, 0)
        self.senha_entry.setPlaceholderText("Digite a senha")
        self.senha_entry.setEchoMode(QLineEdit.EchoMode.Password)
        aplicar_estilo_widget_auto_ajustavel(self.senha_entry, "lineedit")
        grid_layout.addWidget(self.senha_entry, 1, 1)
        main_layout.addLayout(grid_layout)

        main_layout.addStretch()

        login_btn = QPushButton("🔐 Acessar Ferramenta")
        aplicar_estilo_botao(login_btn, "verde")
        login_btn.clicked.connect(self.attempt_login)
        main_layout.addWidget(login_btn)

    def attempt_login(self):
        """Tenta autenticar o usuário com as credenciais fornecidas."""
        username = self.usuario_entry.text()
        password = self.senha_entry.text()
        if not username or not password:
            show_error(
                "Campos Vazios", "Por favor, preencha usuário e senha.", parent=self
            )
            return

        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        try:
            with get_session() as session:
                user = (
                    session.query(Usuario)
                    .filter_by(nome=username, senha=hashed_password)
                    .first()
                )
                if user and user.role == "admin":
                    g.USUARIO_ID = user.id
                    self.login_successful.emit()
                else:
                    show_error(
                        "Falha na Autenticação",
                        "Credenciais inválidas ou sem permissão.",
                        parent=self,
                    )
                    self.senha_entry.clear()
        except SQLAlchemyError as e:
            logging.error("Erro de banco de dados no login: %s", e)
            show_error(
                "Erro de Banco de Dados", "Não foi possível conectar.", parent=self
            )


class InstancesWidget(QWidget):
    """Widget para a aba de Gerenciamento de Instâncias."""

    def __init__(self, parent=None):
        """Inicializa o widget de gerenciamento de instâncias."""
        super().__init__(parent)
        self.tree_sessoes = QTreeWidget()
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

        self.tree_sessoes.setHeaderLabels(["ID Sessão", "Hostname", "Última Atividade"])
        self.tree_sessoes.setColumnWidth(0, 80)
        self.tree_sessoes.setColumnWidth(1, 130)
        self.tree_sessoes.setColumnWidth(2, 150)
        main_layout.addWidget(self.tree_sessoes)

        action_buttons = self._create_action_buttons()
        main_layout.addWidget(action_buttons)

        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #0078d4; margin-top: 5px;")
        self.status_label.setVisible(False)
        main_layout.addWidget(self.status_label)

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
        aplicar_estilo_botao(atualizar_btn, "azul")
        atualizar_btn.clicked.connect(self._load_sessions)
        buttons_layout.addWidget(atualizar_btn)

        shutdown_btn = QPushButton("⚠️ Shutdown Geral")
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
            self.tree_sessoes.clear()
            sessoes = obter_sessoes_ativas()
            self.label_total_instancias.setText(str(len(sessoes)))
            self.label_ultima_atualizacao.setText(datetime.now().strftime("%H:%M:%S"))
            for sessao in sessoes:
                item = QTreeWidgetItem(
                    [
                        sessao.get("session_id", "N/A")[:8],
                        sessao.get("hostname", "N/A"),
                        sessao.get("last_updated", "N/A"),
                    ]
                )
                self.tree_sessoes.addTopLevelItem(item)
        except (KeyError, AttributeError, TypeError) as e:
            logging.error("Erro ao carregar sessões: %s", e)
            self._set_status_message("Erro ao carregar sessões.")

    def _update_shutdown_status(self, active_sessions: int):
        """Atualiza a mensagem de status durante o shutdown."""
        self._set_status_message(f"Aguardando {active_sessions} instância(s) fechar...")
        QApplication.processEvents()

    def _start_global_shutdown(self):
        """Inicia o processo de encerramento de todas as instâncias."""
        msg = "Todas as instâncias da aplicação serão fechadas. Deseja continuar?"
        if not ask_yes_no("Confirmar Shutdown", msg, parent=self):
            return
        self._set_status_message("Enviando comando de encerramento...")
        QApplication.processEvents()

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


# pylint: disable=R0902


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
        self.file_path_entry.setReadOnly(True)
        file_layout.addWidget(self.file_path_entry)

        select_button = QPushButton("Selecionar...")
        aplicar_estilo_botao(select_button, "azul")
        select_button.clicked.connect(self._select_file)
        file_layout.addWidget(select_button)
        layout.addWidget(file_group)

        layout.addStretch()

        self.update_button.setEnabled(False)
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
        self.progress_bar.setStyleSheet(obter_estilo_progress_bar())
        layout.addStretch(1)
        layout.addWidget(self.progress_status_label)
        layout.addWidget(self.progress_bar)
        layout.addStretch(2)
        return widget

    def _update_progress_ui(self, message: str, value: int):
        """Callback para atualizar a UI de progresso."""
        self.progress_status_label.setText(message)
        self.progress_bar.setValue(value)
        QApplication.processEvents()

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
        QApplication.setOverrideCursor(Qt.WaitCursor)
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
        self.list_usuario = QTreeWidget()
        self.toggle_role_btn = None
        self.resetar_senha_btn = None
        self.excluir_btn = None
        g.USUARIO_BUSCA_ENTRY = self.usuario_busca_entry
        g.LIST_USUARIO = self.list_usuario
        self._setup_ui()
        self._listar_usuarios()
        self.list_usuario.itemSelectionChanged.connect(self._update_buttons_state)
        self._update_buttons_state()

    def _setup_ui(self):
        """Configura a interface do usuário para o widget."""
        main_layout = QVBoxLayout(self)
        aplicar_medida_borda_espaco(main_layout, 10, 10)
        self._create_search_frame(main_layout)
        self._create_tree_widget(main_layout)
        self._create_action_buttons(main_layout)

    def _listar_usuarios(self):
        """Busca os usuários no banco de dados e atualiza a lista na interface."""
        try:
            with get_session() as session:
                self.list_usuario.clear()
                usuarios = session.query(Usuario).order_by(Usuario.nome).all()
                for usuario in usuarios:
                    senha_resetada = "Sim" if usuario.senha == "nova_senha" else "Não"
                    item = QTreeWidgetItem(
                        [str(usuario.id), usuario.nome, usuario.role, senha_resetada]
                    )
                    self.list_usuario.addTopLevelItem(item)
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
        self.usuario_busca_entry.textChanged.connect(lambda: buscar("usuario"))
        busca_layout.addWidget(self.usuario_busca_entry, 0, 1)
        limpar_btn = QPushButton("🧹 Limpar")
        aplicar_estilo_botao(limpar_btn, "amarelo")
        limpar_btn.clicked.connect(self._limpar_busca_action)
        busca_layout.addWidget(limpar_btn, 0, 2)
        atualizar_btn = QPushButton("🔄")
        atualizar_btn.setToolTip("Atualizar lista de usuários")
        atualizar_btn.setFixedWidth(40)
        aplicar_estilo_botao(atualizar_btn, "azul")
        atualizar_btn.clicked.connect(self._listar_usuarios)
        busca_layout.addWidget(atualizar_btn, 0, 3)
        main_layout.addWidget(frame_busca)

    def _limpar_busca_action(self):
        """Limpa o campo de busca e recarrega a lista completa de usuários."""
        self.usuario_busca_entry.clear()
        self._listar_usuarios()

    def _create_tree_widget(self, main_layout):
        """Cria o TreeWidget para listar usuários."""
        g.LIST_USUARIO.setHeaderLabels(["Id", "Nome", "Permissões", "Senha Resetada"])
        g.LIST_USUARIO.setColumnHidden(0, True)
        g.LIST_USUARIO.setColumnWidth(1, 120)
        g.LIST_USUARIO.setColumnWidth(2, 80)
        g.LIST_USUARIO.setColumnWidth(3, 100)
        main_layout.addWidget(g.LIST_USUARIO)

    def _create_action_buttons(self, main_layout):
        """Cria os botões de ação."""
        container = QWidget()
        buttons_layout = QHBoxLayout(container)
        aplicar_medida_borda_espaco(buttons_layout, 0)
        buttons_layout.setSpacing(10)
        self.toggle_role_btn = QPushButton("👤 Alterar Permissão")
        aplicar_estilo_botao(self.toggle_role_btn, "verde")
        self.toggle_role_btn.clicked.connect(self._toggle_role_action)
        buttons_layout.addWidget(self.toggle_role_btn)
        self.resetar_senha_btn = QPushButton("🔄 Resetar Senha")
        aplicar_estilo_botao(self.resetar_senha_btn, "amarelo")
        self.resetar_senha_btn.clicked.connect(self._resetar_senha_action)
        buttons_layout.addWidget(self.resetar_senha_btn)
        self.excluir_btn = QPushButton("🗑️ Excluir")
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
        selected_item = selected_items[0]
        role = selected_item.text(2)
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
        self.setFixedSize(380, 185)
        if ICON_PATH and os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        aplicar_medida_borda_espaco(main_layout, 0, 0)
        self.barra_titulo = BarraTitulo(self, tema=obter_tema_atual())
        self.barra_titulo.titulo.setText("Ferramenta Administrativa")
        main_layout.addWidget(self.barra_titulo)
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        self.auth_widget = AdminAuthWidget()
        self.auth_widget.login_successful.connect(self.show_main_tool)
        self.stacked_widget.addWidget(self.auth_widget)
        self.main_tool_widget = QWidget()
        self.instances_tab = InstancesWidget()
        self.updater_tab = UpdaterWidget()
        self.user_management_tab = UserManagementWidget()
        self._setup_main_tool_ui()
        self.stacked_widget.addWidget(self.main_tool_widget)

    def _setup_main_tool_ui(self):
        """Configura a UI principal da ferramenta com abas."""
        layout = QVBoxLayout(self.main_tool_widget)
        aplicar_medida_borda_espaco(layout, 0, 0)
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("QTabWidget::pane { border: 0; }")
        tab_widget.addTab(self.instances_tab, "🔧 Gerenciar Instâncias")
        tab_widget.addTab(self.user_management_tab, "👥 Gerenciar Usuários")
        tab_widget.addTab(self.updater_tab, "🔄 Atualizador")
        layout.addWidget(tab_widget)

    def show_main_tool(self):
        """Mostra a ferramenta principal após a autenticação."""
        self.setFixedSize(380, 400)
        self.stacked_widget.setCurrentWidget(self.main_tool_widget)

    def closeEvent(self, event):  # pylint: disable=C0103
        """Garante que o timer da aba de instâncias seja parado ao fechar."""
        self.instances_tab.stop_timer()
        event.accept()


def main():
    """Função principal para iniciar a aplicação."""
    setup_logging("admin.log", log_to_console=True)
    logging.info("Ferramenta Administrativa iniciada.")
    app = QApplication(sys.argv)
    aplicar_tema_inicial()
    window = AdminTool()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
