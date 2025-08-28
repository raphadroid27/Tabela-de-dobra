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

from src.config import globals as g
from src.models.models import Usuario
from src.utils.banco_dados import session_scope
from src.utils.controlador import buscar
from src.utils.estilo import (
    aplicar_estilo_botao,
    aplicar_estilo_widget_auto_ajustavel,
    aplicar_tema_inicial,
    obter_estilo_progress_bar,
)
from src.utils.interface import limpar_busca, listar
from src.utils.session_manager import (
    force_shutdown_all_instances,
    obter_sessoes_ativas,
)
from src.utils.update_manager import get_installed_version, run_update_process
from src.utils.utilitarios import (
    ICON_PATH,
    aplicar_medida_borda_espaco,
    ask_yes_no,
    setup_logging,
    show_error,
    show_info,
    show_warning,
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
        aplicar_medida_borda_espaco(main_layout, 20, 10)
        main_layout.setAlignment(Qt.AlignCenter)

        title_label = QLabel("Ferramenta de Administração")
        title_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        grid_layout = QGridLayout()
        grid_layout.setVerticalSpacing(10)
        grid_layout.setHorizontalSpacing(10)
        grid_layout.addWidget(QLabel("Usuário Admin:"), 0, 0)
        self.usuario_entry.setPlaceholderText("Digite o usuário")
        aplicar_estilo_widget_auto_ajustavel(self.usuario_entry, "lineedit")
        grid_layout.addWidget(self.usuario_entry, 0, 1)

        grid_layout.addWidget(QLabel("Senha:"), 1, 0)
        self.senha_entry.setPlaceholderText("Digite a senha")
        self.senha_entry.setEchoMode(QLineEdit.Password)
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
            show_error("Campos Vazios",
                       "Por favor, preencha usuário e senha.", parent=self)
            return

        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        with session_scope() as (db_session, _):
            if not db_session:
                show_error("Erro de Banco de Dados",
                           "Não foi possível conectar.", parent=self)
                return
            user = db_session.query(Usuario).filter_by(
                nome=username, senha=hashed_password).first()
            if user and user.role == "admin":
                self.login_successful.emit()
            else:
                show_error("Falha na Autenticação",
                           "Credenciais inválidas ou sem permissão.", parent=self)
                self.senha_entry.clear()


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
        main_layout = QGridLayout(self)
        aplicar_medida_borda_espaco(main_layout, 5)

        frame_info = self._create_info_frame()
        main_layout.addWidget(frame_info, 0, 0, 1, 3)

        frame_sessoes = self._create_sessions_frame()
        main_layout.addWidget(frame_sessoes, 1, 0, 1, 3)

        self._create_action_buttons(main_layout)

        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #0078d4; margin-top: 5px;")
        main_layout.addWidget(self.status_label, 3, 0, 1, 3)

    def _create_info_frame(self):
        """Cria o frame de informações do sistema."""
        frame = QGroupBox("ℹ️ Informações do Sistema")
        layout = QGridLayout(frame)
        layout.addWidget(QLabel("Total de Instâncias Ativas:"), 0, 0)
        self.label_total_instancias.setStyleSheet("font-weight: bold; color: #0078d4;")
        layout.addWidget(self.label_total_instancias, 0, 1)
        layout.addWidget(QLabel("Última Atualização:"), 1, 0)
        layout.addWidget(self.label_ultima_atualizacao, 1, 1)
        return frame

    def _create_sessions_frame(self):
        """Cria o frame que exibe as instâncias ativas."""
        frame = QGroupBox("🖥️ Instâncias Ativas")
        layout = QVBoxLayout(frame)
        self.tree_sessoes.setHeaderLabels(["ID Sessão", "Hostname", "Última Atividade"])
        self.tree_sessoes.setColumnWidth(0, 80)
        self.tree_sessoes.setColumnWidth(1, 130)
        self.tree_sessoes.setColumnWidth(2, 150)
        layout.addWidget(self.tree_sessoes)
        return frame

    def _create_action_buttons(self, layout):
        """Cria os botões de ação (Atualizar, Shutdown Geral)."""
        atualizar_btn = QPushButton("🔄 Atualizar")
        aplicar_estilo_botao(atualizar_btn, "azul")
        atualizar_btn.clicked.connect(self._load_sessions)
        layout.addWidget(atualizar_btn, 2, 0)

        shutdown_btn = QPushButton("⚠️ Shutdown Geral")
        aplicar_estilo_botao(shutdown_btn, "vermelho")
        shutdown_btn.clicked.connect(self._start_global_shutdown)
        layout.addWidget(shutdown_btn, 2, 1, 1, 2)

    def _initialize_data(self):
        """Inicializa os dados e o timer de atualização."""
        self._load_sessions()
        self.timer_atualizacao.timeout.connect(self._load_sessions)
        self.timer_atualizacao.start(60000)  # 60 segundos

    def _load_sessions(self):
        """Carrega e exibe as sessões ativas."""
        try:
            self.tree_sessoes.clear()
            sessoes = obter_sessoes_ativas()
            self.label_total_instancias.setText(str(len(sessoes)))
            self.label_ultima_atualizacao.setText(datetime.now().strftime("%H:%M:%S"))
            for sessao in sessoes:
                item = QTreeWidgetItem([
                    sessao.get("session_id", "N/A")[:8],
                    sessao.get("hostname", "N/A"),
                    sessao.get("last_updated", "N/A"),
                ])
                self.tree_sessoes.addTopLevelItem(item)
        except (KeyError, AttributeError, TypeError) as e:
            logging.error("Erro ao carregar sessões: %s", e)
            self.status_label.setText("Erro ao carregar sessões.")

    def _update_shutdown_status(self, active_sessions: int):
        """Atualiza a mensagem de status durante o shutdown."""
        self.status_label.setText(
            f"Aguardando {active_sessions} instância(s) fechar...")
        QApplication.processEvents()

    def _start_global_shutdown(self):
        """Inicia o processo de encerramento de todas as instâncias."""
        msg = "Todas as instâncias da aplicação serão fechadas. Deseja continuar?"
        if not ask_yes_no("Confirmar Shutdown", msg, parent=self):
            return
        self.status_label.setText("Enviando comando de encerramento...")
        QApplication.processEvents()
        with session_scope() as (db_session, model):
            if not db_session:
                show_error(
                    "Erro de DB", "Não foi possível conectar ao banco de dados.", parent=self)
                return
            success = force_shutdown_all_instances(
                db_session, model, self._update_shutdown_status)

        if success:
            show_info(
                "Sucesso", "Todas as instâncias foram encerradas com sucesso.", parent=self)
            self.status_label.setText("Encerramento concluído com sucesso.")
        else:
            show_error("Timeout", "As instâncias não fecharam a tempo.", parent=self)
            self.status_label.setText("Falha no encerramento (timeout).")

        self._load_sessions()
        QTimer.singleShot(5000, self.status_label.clear)

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
        self.stacked_widget.addWidget(self.main_view)
        self.stacked_widget.addWidget(self.progress_view)
        main_layout.addWidget(self.stacked_widget)

    def _load_current_version(self):
        """Carrega e exibe a versão atualmente instalada."""
        current_version = get_installed_version()
        if current_version:
            self.version_label.setText(f"Versão Instalada: {current_version}")
        else:
            self.version_label.setText("Versão Instalada: Desconhecida")

    def _create_main_view(self):
        """Cria a view principal para seleção de arquivo."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        aplicar_medida_borda_espaco(layout, 10, 10)
        layout.setAlignment(Qt.AlignCenter)

        self.version_label.setAlignment(Qt.AlignCenter)
        self.version_label.setStyleSheet("font-size: 14px; margin-bottom: 15px;")
        layout.addWidget(self.version_label)

        file_group = QGroupBox("Selecionar Pacote de Atualização (.zip)")
        file_layout = QHBoxLayout(file_group)
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
        layout.setAlignment(Qt.AlignCenter)
        self.progress_status_label = QLabel("Iniciando atualização...")
        self.progress_status_label.setAlignment(Qt.AlignCenter)
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

    def start_update_process(self):
        """Inicia o processo de atualização da aplicação."""
        if not self.selected_file_path:
            show_error("Erro", "Nenhum arquivo de atualização selecionado.", parent=self)
            return

        msg = "A aplicação e suas instâncias serão fechadas. Deseja prosseguir?"
        if not ask_yes_no("Confirmar Atualização", msg, parent=self):
            return

        self.stacked_widget.setCurrentWidget(self.progress_view)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            run_update_process(self.selected_file_path, self._update_progress_ui)
            # A aplicação será reiniciada pela função de atualização
            # e esta instância do admin será fechada.
            time.sleep(2)  # Dá tempo para o usuário ler a mensagem final
            QApplication.instance().quit()
        except (ValueError, ConnectionError, RuntimeError, IOError) as e:
            logging.error("Erro no processo de atualização: %s", e)
            show_error("Erro de Atualização", f"Ocorreu um erro: {e}", parent=self)
            self.stacked_widget.setCurrentWidget(self.main_view)
        finally:
            QApplication.restoreOverrideCursor()


class UserManagementWidget(QWidget):
    """Widget para a aba de Gerenciamento de Usuários."""

    def __init__(self, parent=None):
        """Inicializa o widget de gerenciamento de usuários."""
        super().__init__(parent)
        self.usuario_busca_entry = QLineEdit()
        self.list_usuario = QTreeWidget()

        g.USUARIO_BUSCA_ENTRY = self.usuario_busca_entry
        g.LIST_USUARIO = self.list_usuario

        self._setup_ui()
        listar("usuario")

    def _setup_ui(self):
        """Configura a interface do usuário para o widget."""
        main_layout = QGridLayout(self)
        aplicar_medida_borda_espaco(main_layout, 10)

        self._create_search_frame(main_layout)
        self._create_tree_widget(main_layout)
        self._create_action_buttons(main_layout)

    def _create_search_frame(self, main_layout):
        """Cria o frame de busca de usuários."""
        frame_busca = QGroupBox("Filtrar Usuários")
        busca_layout = QGridLayout(frame_busca)

        busca_layout.addWidget(QLabel("Usuário:"), 0, 0)

        self.usuario_busca_entry.textChanged.connect(lambda: buscar("usuario"))
        busca_layout.addWidget(self.usuario_busca_entry, 0, 1)

        limpar_btn = QPushButton("🧹 Limpar")
        aplicar_estilo_botao(limpar_btn, "amarelo")
        limpar_btn.clicked.connect(lambda: limpar_busca("usuario"))
        busca_layout.addWidget(limpar_btn, 0, 2)

        main_layout.addWidget(frame_busca, 0, 0, 1, 3)

    def _create_tree_widget(self, main_layout):
        """Cria o TreeWidget para listar usuários."""
        g.LIST_USUARIO.setHeaderLabels(["Id", "Nome", "Permissões", "Senha Resetada"])
        g.LIST_USUARIO.setColumnHidden(0, True)
        g.LIST_USUARIO.setColumnWidth(1, 120)
        g.LIST_USUARIO.setColumnWidth(2, 80)
        g.LIST_USUARIO.setColumnWidth(3, 100)
        main_layout.addWidget(g.LIST_USUARIO, 1, 0, 1, 3)

    def _create_action_buttons(self, main_layout):
        """Cria os botões de ação."""
        tornar_editor_btn = QPushButton("👤 Tornar Editor")
        aplicar_estilo_botao(tornar_editor_btn, "verde")
        tornar_editor_btn.clicked.connect(self._tornar_editor)
        main_layout.addWidget(tornar_editor_btn, 2, 0)

        resetar_senha_btn = QPushButton("🔄 Resetar Senha")
        aplicar_estilo_botao(resetar_senha_btn, "amarelo")
        resetar_senha_btn.clicked.connect(self._resetar_senha)
        main_layout.addWidget(resetar_senha_btn, 2, 1)

        excluir_btn = QPushButton("🗑️ Excluir")
        aplicar_estilo_botao(excluir_btn, "vermelho")
        excluir_btn.clicked.connect(self._excluir_usuario)
        main_layout.addWidget(excluir_btn, 2, 2)

    def _item_selecionado_usuario(self):
        """Retorna o ID do usuário selecionado na lista."""
        selected_items = g.LIST_USUARIO.selectedItems()
        if not selected_items:
            return None
        try:
            return int(selected_items[0].text(0))
        except (ValueError, IndexError):
            return None

    def _resetar_senha(self):
        """Reseta a senha do usuário selecionado."""
        user_id = self._item_selecionado_usuario()
        if user_id is None:
            show_warning(
                "Aviso", "Selecione um usuário para resetar a senha.", parent=self)
            return

        with session_scope() as (session, _):
            usuario_obj = session.query(Usuario).filter_by(id=user_id).first()
            if usuario_obj:
                usuario_obj.senha = "nova_senha"
                session.commit()
                show_info("Sucesso", "Senha resetada com sucesso.", parent=self)
                listar("usuario")
            else:
                show_error("Erro", "Usuário não encontrado.", parent=self)

    def _excluir_usuario(self):
        """Exclui o usuário selecionado."""
        user_id = self._item_selecionado_usuario()
        if user_id is None:
            show_warning("Aviso", "Selecione um usuário para excluir.", parent=self)
            return

        if not ask_yes_no("Atenção!", "Tem certeza que deseja excluir o usuário?", parent=self):
            return

        try:
            with session_scope() as (session, _):
                usuario_obj = session.query(Usuario).filter_by(id=user_id).first()
                if usuario_obj:
                    session.delete(usuario_obj)
                    session.commit()
                    show_info("Sucesso", "Usuário excluído com sucesso!", parent=self)
                    listar("usuario")
        except SQLAlchemyError as e:
            show_error(
                "Erro", f"Erro de banco de dados ao excluir usuário: {e}", parent=self)

    def _tornar_editor(self):
        """Promove o usuário selecionado a editor."""
        user_id = self._item_selecionado_usuario()
        if user_id is None:
            show_warning(
                "Aviso", "Selecione um usuário para promover a editor.", parent=self)
            return

        with session_scope() as (session, _):
            usuario_obj = session.query(Usuario).filter_by(id=user_id).first()
            if not usuario_obj:
                show_error("Erro", "Usuário não encontrado.", parent=self)
                return

            if usuario_obj.role == "admin":
                show_error("Erro", "O usuário já é um administrador.", parent=self)
                return
            if usuario_obj.role == "editor":
                show_info("Informação", "O usuário já é um editor.", parent=self)
                return

            usuario_obj.role = "editor"
            session.commit()
            show_info("Sucesso", "Usuário promovido a editor com sucesso.", parent=self)
            listar("usuario")


class AdminTool(QMainWindow):
    """Janela principal da Ferramenta de Administração."""

    def __init__(self):
        """Inicializa a janela principal."""
        super().__init__()
        self.setWindowTitle("Ferramenta de Administração")
        self.setFixedSize(450, 450)
        if ICON_PATH and os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

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
        tab_widget = QTabWidget()
        tab_widget.addTab(self.instances_tab, "🔧 Gerenciar Instâncias")
        tab_widget.addTab(self.updater_tab, "🔄 Atualizador")
        tab_widget.addTab(self.user_management_tab, "👥 Gerenciar Usuários")
        layout.addWidget(tab_widget)

    def show_main_tool(self):
        """Mostra a ferramenta principal após a autenticação."""
        self.stacked_widget.setCurrentWidget(self.main_tool_widget)

    def closeEvent(self, event):  # pylint: disable=C0103
        """Garante que o timer da aba de instâncias seja parado ao fechar."""
        self.instances_tab.stop_timer()
        event.accept()


def main():
    """Função principal para iniciar a aplicação."""
    setup_logging("admin.log", log_to_console=True)
    logging.info("Ferramenta de Administração iniciada.")
    app = QApplication(sys.argv)
    aplicar_tema_inicial()
    window = AdminTool()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
