"""
Updater Gráfico para a Aplicação de Cálculo de Dobra.
"""

import hashlib
import logging
import os
import shutil
import subprocess

# --- Importações da Biblioteca Padrão ---
import sys
import time
import zipfile
from datetime import datetime, timezone
from typing import Any, Type

from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtGui import QIcon

# --- Importações de Terceiros ---
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QStyle,
    QVBoxLayout,
    QWidget,
)

# --- Configuração de constantes ---
# SHUTDOWN_WAIT_SECONDS define o tempo de espera (em segundos) após enviar o comando de shutdown
# para garantir que todas as instâncias da aplicação tenham tempo suficiente para encerrar
# antes de prosseguir com a atualização. Ajuste conforme necessário para ambientes diferentes.
SHUTDOWN_WAIT_SECONDS = 3  # Tempo de espera após comando de shutdown

# --- LÓGICA DE BOOTSTRAP: Encontrar o diretório base ANTES de outras importações ---


def obter_dir_base_local():
    """
    Determina o diretório base. Lógica específica para o updater.py
    que reside na raiz do projeto.
    """
    if getattr(sys, "frozen", False):
        # Modo compilado (updater.exe)
        return os.path.dirname(sys.executable)
    # Modo de script (python updater.py)
    return os.path.dirname(os.path.abspath(__file__))


# Adiciona o diretório ao path para que as importações de 'src' funcionem
BASE_DIR = obter_dir_base_local()
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
# --- FIM DO BOOTSTRAP ---

try:
    # --- Importações da Aplicação Local (Agora funcionam) ---
    from src.components.barra_titulo import BarraTitulo
    from src.models.models import SystemControl as SystemControlModel
    from src.models.models import Usuario
    from src.utils.banco_dados import session_scope
    from src.utils.estilo import (
        aplicar_estilo_botao,
        aplicar_estilo_widget_auto_ajustavel,
        aplicar_tema_inicial,
        obter_estilo_progress_bar,
        obter_tema_atual,
    )
    from src.utils.update_manager import (
        checar_updates,
        download_update,
        get_installed_version,
    )
    from src.utils.utilitarios import (
        APP_EXECUTABLE_PATH,
        ICON_PATH,
        UPDATE_TEMP_DIR,
        aplicar_medida_borda_espaco,
        setup_logging,
        show_error,
    )

except ImportError as e:
    # Fallback de emergência
    logging.basicConfig(
        level=logging.CRITICAL, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logging.critical("Erro de Importação: %s. BASE_DIR: %s", e, BASE_DIR)
    QApplication(sys.argv)
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setText(
        "Erro Crítico de Inicialização:\n"
        f"Não foi possível encontrar os módulos da aplicação.\n\n{e}\n\n"
        "Verifique se o updater.exe está na pasta correta."
    )
    msg.setWindowTitle("Erro de Módulo")
    msg.exec()
    sys.exit(1)


class AdminAuthWidget(QWidget):
    """
    Widget para autenticação de administrador, para ser embutido em outras janelas.
    """

    # Sinais para comunicar o resultado para a janela pai
    login_successful = Signal()
    login_cancelled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.usuario_entry = None
        self.senha_entry = None
        self._setup_ui()
        self.usuario_entry.setFocus()

    def _setup_ui(self):
        """Configura a interface do widget de autenticação."""
        main_layout = QVBoxLayout(self)
        aplicar_medida_borda_espaco(main_layout, 10, 10)
        main_layout.setAlignment(Qt.AlignCenter)

        # Título
        title_label = QLabel("Autenticação de Admin")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Grid para os campos
        grid_layout = QGridLayout()
        grid_layout.setVerticalSpacing(10)
        grid_layout.setHorizontalSpacing(10)

        grid_layout.addWidget(QLabel("Usuário:"), 0, 0)
        self.usuario_entry = QLineEdit()
        self.usuario_entry.setPlaceholderText("Digite o usuário admin")
        self.usuario_entry.setToolTip("Usuário admin para autenticação")
        aplicar_estilo_widget_auto_ajustavel(self.usuario_entry, "lineedit")
        grid_layout.addWidget(self.usuario_entry, 0, 1)

        grid_layout.addWidget(QLabel("Senha:"), 1, 0)
        self.senha_entry = QLineEdit()
        self.senha_entry.setPlaceholderText("Digite a senha")
        self.senha_entry.setEchoMode(QLineEdit.Password)
        self.senha_entry.setToolTip("Senha do usuário admin")
        aplicar_estilo_widget_auto_ajustavel(self.senha_entry, "lineedit")
        grid_layout.addWidget(self.senha_entry, 1, 1)

        main_layout.addLayout(grid_layout)
        main_layout.addStretch(1)

        # Layout para os botões
        button_layout = QHBoxLayout()
        aplicar_medida_borda_espaco(button_layout, 0, 10)

        cancel_btn = QPushButton("Cancelar")
        aplicar_estilo_botao(cancel_btn, "vermelho")
        cancel_btn.setToolTip("Clique para cancelar o login")
        cancel_btn.clicked.connect(self.login_cancelled.emit)

        login_btn = QPushButton("🔐 Login")
        aplicar_estilo_botao(login_btn, "verde")
        login_btn.setToolTip("Clique para fazer login como administrador")
        login_btn.clicked.connect(self.attempt_login)

        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(login_btn)
        main_layout.addLayout(button_layout)

    def attempt_login(self):
        """Valida as credenciais e emite um sinal correspondente."""
        username = self.usuario_entry.text()
        password = self.senha_entry.text()

        if not username or not password:
            show_error(
                "Campos Vazios", "Por favor, preencha usuário e senha.", parent=self
            )
            return

        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        with session_scope() as (db_session, _):
            if not db_session:
                show_error(
                    "Erro de Banco de Dados",
                    "Não foi possível conectar ao banco de dados.",
                    parent=self,
                )
                return

            user = (
                db_session.query(Usuario)
                .filter_by(nome=username, senha=hashed_password)
                .first()
            )

            if user and user.role == "admin":
                self.login_successful.emit()
            else:
                show_error(
                    "Falha na Autenticação",
                    "Credenciais inválidas ou o usuário não é um administrador.",
                    parent=self,
                )
                self.senha_entry.clear()


# pylint: disable=too-many-instance-attributes


class UpdaterWindow(QMainWindow):
    """Janela principal da interface do Updater com múltiplas telas."""

    def __init__(self, mode="check"):
        super().__init__()
        self.update_info = None
        self.mode = mode

        # Inicializa os atributos que serão definidos fora do init
        self.central_widget = None
        self.barra_titulo = None
        self.stacked_widget = None
        self.status_view = None
        self.auth_view = None
        self.progress_view = None
        self.status_label = None
        self.version_label = None
        self.update_button = None
        self.cancel_button = None
        self.refresh_button = None
        self.progress_status_label = None
        self.progress_bar = None

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setFixedSize(360, 180)
        if ICON_PATH and os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))

        self.setup_ui()
        self.connect_signals()
        QTimer.singleShot(100, self.force_check_for_updates)

    def setup_ui(self):
        """Configura os widgets e o layout com QStackedWidget."""
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_layout = QVBoxLayout(self.central_widget)
        aplicar_medida_borda_espaco(main_layout, 0, 0)

        self.barra_titulo = BarraTitulo(self, tema=obter_tema_atual())
        self.barra_titulo.titulo.setText("Atualizador")

        refresh_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload)
        self.refresh_button = QPushButton(icon=refresh_icon)
        self.refresh_button.setToolTip(
            "Recarregar e verificar novamente por atualizações"
        )
        self.refresh_button.setFlat(True)
        self.refresh_button.setFixedSize(28, 28)
        self.refresh_button.setIconSize(QSize(16, 16))
        self.refresh_button.setCursor(Qt.PointingHandCursor)

        title_layout = self.barra_titulo.layout()
        if title_layout and isinstance(title_layout, QHBoxLayout):
            insert_position = title_layout.count() - 2
            if insert_position < 0:
                insert_position = title_layout.count()
            title_layout.insertWidget(insert_position, self.refresh_button)

        main_layout.addWidget(self.barra_titulo)

        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        self.status_view = self._create_status_view()
        self.stacked_widget.addWidget(self.status_view)

        self.auth_view = AdminAuthWidget()
        self.stacked_widget.addWidget(self.auth_view)

        self.progress_view = self._create_progress_view()
        self.stacked_widget.addWidget(self.progress_view)

    def _create_status_view(self) -> QWidget:
        """Cria o widget da tela de status."""

        widget = QWidget()
        layout = QVBoxLayout(widget)
        aplicar_medida_borda_espaco(layout, 10, 10)
        layout.setAlignment(Qt.AlignCenter)

        self.status_label = QLabel("Verificando atualizações...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold;")

        self.version_label = QLabel("")
        self.version_label.setAlignment(Qt.AlignCenter)
        self.version_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #55aaff;"
        )

        layout.addWidget(self.status_label)
        layout.addWidget(self.version_label)
        layout.addStretch()

        button_layout = QHBoxLayout()
        aplicar_medida_borda_espaco(button_layout, 0, 10)

        self.cancel_button = QPushButton("Cancelar")
        aplicar_estilo_botao(self.cancel_button, "vermelho")
        self.cancel_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cancel_button.setToolTip("Cancelar a atualização")

        self.update_button = QPushButton("Atualizar Agora")
        self.update_button.setEnabled(False)
        self.update_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.update_button.setToolTip(
            "Clique para iniciar o processo de atualização após autenticação"
        )

        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.update_button)

        layout.addLayout(button_layout)

        return widget

    def _create_progress_view(self) -> QWidget:
        """Cria o widget da tela de progresso."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        aplicar_medida_borda_espaco(layout, 10, 10)
        layout.setAlignment(Qt.AlignCenter)

        self.progress_status_label = QLabel("Iniciando atualização...")
        self.progress_status_label.setAlignment(Qt.AlignCenter)
        self.progress_status_label.setStyleSheet("font-size: 16px;")

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(obter_estilo_progress_bar())

        layout.addStretch(1)
        layout.addWidget(self.progress_status_label)
        layout.addWidget(self.progress_bar)
        layout.addStretch(2)

        return widget

    def connect_signals(self):
        """Conecta todos os sinais aos seus slots."""
        self.cancel_button.clicked.connect(self.close)
        self.update_button.clicked.connect(self.request_authentication)
        self.refresh_button.clicked.connect(self.force_check_for_updates)
        self.auth_view.login_successful.connect(self.on_login_success)
        self.auth_view.login_cancelled.connect(self.on_login_cancel)

    def force_check_for_updates(self):
        """Executa a lógica para checar atualizações, mostrando feedback visual."""
        logging.info("Verificação de atualização forçada pelo usuário.")
        self.status_label.setText("Verificando atualizações...")
        self.version_label.setText("")
        self.update_button.setEnabled(False)
        self.update_button.setStyleSheet("")
        QApplication.setOverrideCursor(Qt.WaitCursor)

        QTimer.singleShot(100, self._check_and_update_ui)

    def _check_and_update_ui(self):
        """Função auxiliar que realmente faz a verificação."""
        try:
            current_version = get_installed_version()
            if not current_version:
                self.status_label.setText("Erro ao ler a versão local.")
                self.version_label.setText("Verifique o banco de dados.")
                self.update_button.setEnabled(False)
                return

            self.update_info = checar_updates(current_version)

            if self.update_info:
                self.show_update_available()
            else:
                self.show_no_update(current_version)

            if self.mode == "apply" and self.update_info:
                self.request_authentication()
                self.mode = "check"
        finally:
            QApplication.restoreOverrideCursor()

    def show_update_available(self):
        """
        Mostra a mensagem de que uma nova atualização está disponível.

        Apenas ADMINS veem esta interface. Usuários comuns nunca abrem o updater
        diretamente - eles apenas recebem notificações via UpdateNotificationDialog.
        """
        latest_version = self.update_info.get("ultima_versao", "N/A")
        self.status_label.setText("Nova versão disponível!")
        self.version_label.setText(f"Versão {latest_version}")
        self.update_button.setEnabled(True)
        aplicar_estilo_botao(self.update_button, "azul")

    def show_no_update(self, current_version: str):
        """Mostra a mensagem de que o aplicativo já está atualizado."""
        self.status_label.setText("O seu aplicativo está atualizado.")
        self.version_label.setText(f"Versão atual: {current_version}")
        self.update_button.setEnabled(False)
        self.update_button.setStyleSheet("")
        self.cancel_button.setText("Fechar")

    def request_authentication(self):
        """
        Verifica novamente se há atualizações antes de solicitar a autenticação.
        """
        logging.info(
            "Botão 'Atualizar Agora' clicado. Verificando novamente o arquivo de versão."
        )
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            current_version = get_installed_version()
            if not current_version:
                show_error(
                    "Erro", "Não foi possível ler a versão instalada do banco de dados."
                )
                return
            self.update_info = checar_updates(current_version)

            if self.update_info:
                logging.info("Atualização confirmada. Solicitando autenticação.")
                self.stacked_widget.setCurrentWidget(self.auth_view)
            else:
                logging.warning(
                    "Nenhuma atualização encontrada após a nova verificação."
                )
                self.show_no_update(current_version)
                QMessageBox.information(
                    self,
                    "Atualizado",
                    "O aplicativo já está na versão mais recente. "
                    "Nenhuma atualização é necessária.",
                )
        finally:
            QApplication.restoreOverrideCursor()

    def on_login_success(self):
        """
        Inicia o processo de atualização após o ADMIN fazer login com sucesso.

        Hierarquia clara:
        - ADMIN: Tem controle total, pode iniciar atualizações
        - USUÁRIOS: Não veem esta tela, apenas recebem notificações
        """
        reply = QMessageBox.question(
            self,
            "Confirmar Atualização",
            "O aplicativo principal e todas as suas instâncias serão "
            "fechadas para continuar.\n\nDeseja prosseguir?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.No:
            self.stacked_widget.setCurrentWidget(self.status_view)
            return

        self.stacked_widget.setCurrentWidget(self.progress_view)
        QApplication.setOverrideCursor(Qt.WaitCursor)

        try:
            self.run_update_steps()
        except (ValueError, ConnectionError, RuntimeError, IOError, OSError) as e:
            logging.error("Erro no processo de atualização: %s", e)
            show_error("Erro de Atualização", f"Ocorreu um erro: {e}", parent=self)
            self.progress_status_label.setText("Falha na atualização.")
            self.stacked_widget.setCurrentWidget(self.status_view)
        finally:
            QApplication.restoreOverrideCursor()

    def on_login_cancel(self):
        """Retorna para a tela de status se o login for cancelado."""
        self.stacked_widget.setCurrentWidget(self.status_view)

    def run_update_steps(self):
        """Executa as etapas sequenciais da atualização."""

        self.progress_status_label.setText("A baixar ficheiros...")
        self.progress_bar.setValue(10)
        QApplication.processEvents()
        zip_filename = self.update_info.get("nome_arquivo")
        if not zip_filename:
            raise ValueError("Nome do ficheiro de atualização não encontrado.")
        download_update(zip_filename)
        self.progress_bar.setValue(40)

        self.progress_status_label.setText("A fechar a aplicação principal...")
        QApplication.processEvents()

        # Aguarda um pouco para que as instâncias detectem o sinal
        time.sleep(3)

        with session_scope() as (db_session, model):
            if not db_session or not model:
                raise ConnectionError("Não foi possível ligar à base de dados.")
            if not self.force_shutdown_all_instances(db_session, model):
                raise RuntimeError(
                    "Não foi possível fechar as instâncias da aplicação."
                )
        self.progress_bar.setValue(70)

        self.progress_status_label.setText("A aplicar a atualização...")
        QApplication.processEvents()
        if not self.apply_update(zip_filename):
            raise IOError("Falha ao aplicar os ficheiros de atualização.")
        self.progress_bar.setValue(90)

        self.progress_status_label.setText("Atualização concluída! A reiniciar...")
        self.progress_bar.setValue(100)
        QApplication.processEvents()
        time.sleep(2)
        self.start_application()
        self.close()

    def force_shutdown_all_instances(
        self, session: Any, model: Type[SystemControlModel]
    ) -> bool:
        """Força o encerramento de todas as instâncias da aplicação."""
        logging.info("A enviar comando de encerramento...")
        try:
            cmd_entry = session.query(model).filter_by(key="UPDATE_CMD").first()
            if cmd_entry:
                cmd_entry.value = "SHUTDOWN"
                cmd_entry.last_updated = datetime.now(timezone.utc)
            else:
                new_cmd = model(key="UPDATE_CMD", value="SHUTDOWN", type="COMMAND")
                session.add(new_cmd)
            session.commit()

            start_time = time.time()
            while (time.time() - start_time) < 60:
                active_sessions = session.query(model).filter_by(type="SESSION").count()
                self.progress_status_label.setText(
                    f"A aguardar {active_sessions} instância(s)..."
                )
                QApplication.processEvents()
                if active_sessions == 0:
                    logging.info("Todas as instâncias foram fechadas.")
                    time.sleep(3)
                    return True
                time.sleep(2)
            logging.error("Timeout! As instâncias não fecharam a tempo.")
            return False
        finally:
            cmd_entry = session.query(model).filter_by(key="UPDATE_CMD").first()
            if cmd_entry and cmd_entry.value == "SHUTDOWN":
                cmd_entry.value = "NONE"
                session.commit()

    def apply_update(self, zip_filename: str) -> bool:
        """Extrai e aplica os ficheiros da atualização."""
        zip_filepath = os.path.join(UPDATE_TEMP_DIR, zip_filename)
        if not os.path.exists(zip_filepath):
            logging.error("Ficheiro de atualização não encontrado em %s", zip_filepath)
            return False

        app_dir = BASE_DIR
        try:
            with zipfile.ZipFile(zip_filepath, "r") as zip_ref:
                extract_path = os.path.join(UPDATE_TEMP_DIR, "extracted")
                if os.path.exists(extract_path):
                    shutil.rmtree(extract_path)
                os.makedirs(extract_path, exist_ok=True)
                zip_ref.extractall(extract_path)

            for item in os.listdir(extract_path):
                src_path = os.path.join(extract_path, item)
                dst_path = os.path.join(app_dir, item)
                try:
                    if os.path.isdir(dst_path):
                        shutil.rmtree(dst_path)
                    elif os.path.isfile(dst_path):
                        os.remove(dst_path)
                    shutil.move(src_path, dst_path)
                except OSError as e:
                    logging.warning("Não foi possível substituir '%s': %s.", item, e)

            logging.info("Atualização aplicada com sucesso!")
            return True
        except (IOError, OSError, zipfile.BadZipFile) as e:
            logging.error("Erro ao aplicar a atualização: %s", e)
            return False
        finally:
            if os.path.isdir(UPDATE_TEMP_DIR):
                try:
                    shutil.rmtree(UPDATE_TEMP_DIR)
                except OSError as e:
                    logging.error(
                        "Não foi possível remover o diretório temporário: %s", e
                    )

    def start_application(self):
        """Inicia a aplicação principal após a atualização."""
        if not os.path.exists(APP_EXECUTABLE_PATH):
            logging.error(
                "Executável da aplicação não encontrado: %s", APP_EXECUTABLE_PATH
            )
            mensagem = f"Não foi possível encontrar o executável principal:\n{APP_EXECUTABLE_PATH}"
            show_error("Erro Crítico", mensagem)
            return
        logging.info("A iniciar a aplicação: %s", APP_EXECUTABLE_PATH)
        try:
            # pylint: disable=consider-using-with
            subprocess.Popen([APP_EXECUTABLE_PATH])

        except OSError as e:
            logging.error("Erro ao iniciar a aplicação: %s", e)
            show_error(
                "Erro ao Reiniciar",
                f"Não foi possível reiniciar a aplicação principal:\n{e}",
            )


def main():
    """Função principal que inicializa e executa o Updater."""
    setup_logging("updater.log", log_to_console=True)
    logging.info("Updater Gráfico iniciado.")

    app = QApplication(sys.argv)
    aplicar_tema_inicial()

    mode = "check"
    if len(sys.argv) > 1 and sys.argv[1] == "--apply":
        mode = "apply"

    window = UpdaterWindow(mode=mode)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
