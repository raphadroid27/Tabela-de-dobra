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

from PySide6.QtCore import QSettings, Qt, QTimer
from PySide6.QtGui import QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.exc import SQLAlchemyError

from src.admin_app.avisos_widget import AvisosWidget
from src.admin_app.instances_widget import InstancesWidget
from src.admin_app.updater_widget import UpdaterWidget
from src.admin_app.users_widget import UserManagementWidget
from src.config import globals as g
from src.forms import form_aut
from src.forms.form_manual import show_manual
from src.models.models import Usuario
from src.utils import ipc_manager
from src.utils.banco_dados import get_session
from src.utils.inactivity_monitor import ativar_monitor_inatividade
from src.utils.theme_manager import theme_manager
from src.utils.themed_widgets import ThemedMainWindow
from src.utils.utilitarios import (
    ICON_PATH,
    aplicar_medida_borda_espaco,
    setup_logging,
    show_error,
)

ADMIN_INACTIVITY_TIMEOUT_MS = 10 * 60 * 1000


def obter_dir_base_local():
    """Determina o diretório base para importações corretas."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = obter_dir_base_local()
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


class AdminTool(ThemedMainWindow):
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
        self.warnings_tab = AvisosWidget()
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
        self.tab_widget.addTab(self.warnings_tab, "⚠️ Gerenciar Avisos")
        self.tab_widget.addTab(self.updater_tab, "🔄 Atualizador")

        self.tab_widget.setTabToolTip(
            0, "Gerenciar instâncias ativas da aplicação (Ctrl+1)"
        )
        self.tab_widget.setTabToolTip(1, "Gerenciar usuários do sistema (Ctrl+2)")
        self.tab_widget.setTabToolTip(
            2, "Gerenciar avisos exibidos na tela inicial (Ctrl+3)")
        self.tab_widget.setTabToolTip(3, "Atualizar a aplicação (Ctrl+4)")

        layout.addWidget(self.tab_widget)

    def _setup_global_shortcuts(self):
        """Configura atalhos globais da aplicação."""
        tab1_shortcut = QShortcut(QKeySequence("Ctrl+1"), self)
        tab1_shortcut.activated.connect(lambda: self.tab_widget.setCurrentIndex(0))

        tab2_shortcut = QShortcut(QKeySequence("Ctrl+2"), self)
        tab2_shortcut.activated.connect(lambda: self.tab_widget.setCurrentIndex(1))

        tab3_shortcut = QShortcut(QKeySequence("Ctrl+3"), self)
        tab3_shortcut.activated.connect(lambda: self.tab_widget.setCurrentIndex(2))

        help_shortcut = QShortcut(QKeySequence("F1"), self)
        help_shortcut.activated.connect(lambda: show_manual(self, "admin"))

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
        ativar_monitor_inatividade(
            self, ADMIN_INACTIVITY_TIMEOUT_MS, self._handle_inactivity_timeout
        )

    def _reset_inactivity_timer(self):
        """Reinicia o timer de inatividade."""
        if hasattr(self, "inactivity_timer"):
            self.inactivity_timer.start()

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
    ipc_manager.ensure_ipc_dirs_exist()
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
