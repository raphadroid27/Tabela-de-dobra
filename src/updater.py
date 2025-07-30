# -*- coding: utf-8 -*-
"""
Updater Gráfico para a Aplicação de Cálculo de Dobra.

Responsável por:
1. Apresentar uma interface gráfica para o processo de atualização.
2. Verificar se existem novas versões disponíveis.
3. Autenticar um usuário 'admin' do aplicativo antes de prosseguir.
4. Baixar e aplicar a atualização, substituindo os arquivos antigos.
5. Forçar o encerramento de instâncias do app principal.
6. Reiniciar o app principal após a atualização.
"""

# --- Importações da Biblioteca Padrão ---
import sys
import os
import subprocess
import zipfile
import time
import shutil
import logging
import hashlib
from datetime import datetime, timezone
from typing import Type

# --- Importações de Terceiros ---
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QLabel, QPushButton, QHBoxLayout, QMessageBox,
                               QInputDialog, QLineEdit)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon

# --- Adiciona o diretório raiz do projeto ao path ---
try:
    BASE_DIR = os.path.dirname(os.path.abspath(
        sys.argv[0] if getattr(sys, 'frozen', False) else __file__))
    if BASE_DIR not in sys.path:
        sys.path.insert(0, BASE_DIR)

    # --- Importações da Aplicação Local (com caminho explícito) ---
    from src import __version__ as APP_VERSION
    from src.models.models import SystemControl as SystemControlModel, Usuario
    from src.utils.banco_dados import session_scope
    from src.utils.update_manager import checar_updates, download_update
    from src.utils.utilitarios import (
        setup_logging, APP_EXECUTABLE_PATH, UPDATE_TEMP_DIR,
        ICON_PATH, show_error
    )
except ImportError as e:
    # Fallback de emergência
    QApplication(sys.argv)
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Critical)
    msg.setText(
        "Erro Crítico de Inicialização:\n"
        f"Não foi possível encontrar os módulos da aplicação.\n\n{e}\n\n"
        "Verifique se o updater.exe está na pasta correta."
    )
    msg.setWindowTitle("Erro de Módulo")
    msg.exec()
    sys.exit(1)


class UpdaterWindow(QMainWindow):
    """Janela principal da interface do Updater."""

    def __init__(self, mode='check'):
        super().__init__()
        self.update_info = None
        self.mode = mode

        self.setup_ui()
        self.setWindowTitle("Atualizador")
        self.setFixedSize(400, 180)

        if ICON_PATH and os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))

        QTimer.singleShot(100, self.run_initial_flow)

    def setup_ui(self):
        """Configura os widgets da interface."""
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setAlignment(Qt.AlignCenter)

        self.status_label = QLabel("Verificando atualizações...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px;")

        self.version_label = QLabel("")
        self.version_label.setAlignment(Qt.AlignCenter)
        self.version_label.setStyleSheet("font-size: 12px; color: #55aaff;")

        self.button_layout = QHBoxLayout()
        self.update_button = QPushButton("Atualizar Agora")
        self.update_button.setEnabled(False)
        self.update_button.clicked.connect(self.start_update_process)

        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.close)

        self.button_layout.addWidget(self.update_button)
        self.button_layout.addWidget(self.cancel_button)

        self.layout.addWidget(self.status_label)
        self.layout.addWidget(self.version_label)
        self.layout.addStretch()
        self.layout.addLayout(self.button_layout)

    def run_initial_flow(self):
        """Executa a lógica inicial baseada no modo de lançamento."""
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self.update_info = checar_updates(APP_VERSION)
            if self.update_info:
                self.show_update_available()
            else:
                self.show_no_update()

            if self.mode == 'apply' and self.update_info:
                self.start_update_process()

        finally:
            QApplication.restoreOverrideCursor()

    def show_update_available(self):
        """Atualiza a UI para mostrar que uma atualização foi encontrada."""
        latest_version = self.update_info.get("ultima_versao", "N/A")
        self.status_label.setText("Nova versão disponível!")
        self.version_label.setText(f"Versão {latest_version}")
        self.update_button.setEnabled(True)
        self.update_button.setStyleSheet(
            "background-color: #007acc; color: white;")

    def show_no_update(self):
        """Atualiza a UI para mostrar que o app está atualizado."""
        self.status_label.setText(
            "O seu aplicativo já está na versão mais recente.")
        self.version_label.setText(f"Versão atual: {APP_VERSION}")
        self.update_button.setEnabled(False)
        self.cancel_button.setText("Fechar")

    def validate_app_admin(self) -> bool:
        """Pede credenciais e valida se o usuário é um admin do app."""
        username, ok1 = QInputDialog.getText(self, "Autenticação Necessária",
                                             "Nome do usuário Administrador:")
        if not ok1 or not username:
            return False

        password, ok2 = QInputDialog.getText(self, "Autenticação Necessária",
                                             f"Senha para o usuário '{username}':",
                                             QLineEdit.Password)
        if not ok2:
            return False

        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        with session_scope() as (db_session, _):
            if not db_session:
                show_error("Erro de Banco de Dados",
                           "Não foi possível conectar ao banco de dados para validar as credenciais.",
                           parent=self)
                return False

            user = db_session.query(Usuario).filter_by(
                nome=username, senha=hashed_password).first()

            if user and user.role == 'admin':
                return True

        show_error("Falha na Autenticação",
                   "As credenciais fornecidas são inválidas ou o usuário não é um administrador.",
                   parent=self)
        return False

    def start_update_process(self):
        """Inicia o fluxo completo de atualização."""
        # 1. Validar se o usuário é um admin do aplicativo
        if not self.validate_app_admin():
            return  # A mensagem de erro já foi mostrada em validate_app_admin

        # 2. Confirmar a ação
        reply = QMessageBox.question(
            self, "Confirmar Atualização",
            "O aplicativo principal e todas as suas instâncias serão "
            "fechadas para continuar.\n\nDeseja prosseguir?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.No:
            return

        # 3. Iniciar o processo visual
        self.update_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        QApplication.setOverrideCursor(Qt.WaitCursor)

        try:
            self.run_update_steps()
        except (ValueError, ConnectionError, RuntimeError,
                IOError, OSError) as e:
            logging.error("Erro no processo de atualização: %s", e)
            show_error("Erro de Atualização",
                       f"Ocorreu um erro: {e}", parent=self)
            self.status_label.setText("Falha na atualização.")
            self.cancel_button.setEnabled(True)
            self.cancel_button.setText("Fechar")
        finally:
            QApplication.restoreOverrideCursor()

    def run_update_steps(self):
        """Executa as etapas sequenciais da atualização."""
        self.status_label.setText("Baixando arquivos...")
        QApplication.processEvents()
        zip_filename = self.update_info.get("nome_arquivo")
        if not zip_filename:
            raise ValueError(
                "Nome do arquivo de atualização não encontrado em versao.json.")
        download_update(zip_filename)

        self.status_label.setText("Fechando aplicativo principal...")
        QApplication.processEvents()
        with session_scope() as (db_session, model):
            if not db_session or not model:
                raise ConnectionError(
                    "Não foi possível conectar ao banco de dados.")
            if not self.force_shutdown_all_instances(db_session, model):
                raise RuntimeError(
                    "Não foi possível fechar todas as instâncias do aplicativo.")

        self.status_label.setText("Aplicando atualização...")
        QApplication.processEvents()
        if not self.apply_update(zip_filename):
            raise IOError(
                "Falha ao aplicar os arquivos de atualização. Verifique as permissões da pasta.")

        self.status_label.setText("Atualização concluída! Reiniciando...")
        QApplication.processEvents()
        time.sleep(2)
        self.start_application()
        self.close()

    def force_shutdown_all_instances(self, session: any, model: Type[SystemControlModel]) -> bool:
        """Envia comando de desligamento e aguarda o fechamento."""
        logging.info("Enviando comando de desligamento...")
        try:
            cmd_entry = session.query(model).filter_by(
                key='UPDATE_CMD').first()
            if cmd_entry:
                cmd_entry.value = 'SHUTDOWN'
                cmd_entry.last_updated = datetime.now(timezone.utc)
                session.commit()

            start_time = time.time()
            while (time.time() - start_time) < 60:
                active_sessions = session.query(
                    model).filter_by(type='SESSION').count()
                self.version_label.setText(
                    f"Aguardando {active_sessions} instância(s) fechar(em)...")
                QApplication.processEvents()
                if active_sessions == 0:
                    logging.info("Todas as instâncias foram fechadas.")
                    time.sleep(3)
                    return True
                time.sleep(2)

            logging.error("Timeout! Instâncias não fecharam a tempo.")
            return False
        finally:
            cmd_entry = session.query(model).filter_by(
                key='UPDATE_CMD').first()
            if cmd_entry and cmd_entry.value == 'SHUTDOWN':
                cmd_entry.value = 'NONE'
                session.commit()

    def apply_update(self, zip_filename: str) -> bool:
        """Extrai e substitui os arquivos da aplicação."""
        zip_filepath = os.path.join(UPDATE_TEMP_DIR, zip_filename)
        if not os.path.exists(zip_filepath):
            logging.error(
                "Arquivo de atualização não encontrado em %s", zip_filepath)
            return False

        app_dir = BASE_DIR
        try:
            with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
                extract_path = os.path.join(UPDATE_TEMP_DIR, 'extracted')
                os.makedirs(extract_path, exist_ok=True)
                zip_ref.extractall(extract_path)

            for item in os.listdir(extract_path):
                src_path = os.path.join(extract_path, item)
                dst_path = os.path.join(app_dir, item)
                if os.path.isdir(dst_path):
                    shutil.rmtree(dst_path)
                elif os.path.isfile(dst_path):
                    os.remove(dst_path)
                shutil.move(src_path, dst_path)

            logging.info("Atualização aplicada com sucesso!")
            return True
        except (IOError, OSError, zipfile.BadZipFile) as e:
            logging.error("Erro ao aplicar a atualização: %s", e)
            return False
        finally:
            if os.path.isdir(UPDATE_TEMP_DIR):
                shutil.rmtree(UPDATE_TEMP_DIR)

    def start_application(self):
        """Inicia a aplicação principal (app.exe)."""
        if not os.path.exists(APP_EXECUTABLE_PATH):
            logging.error(
                "Executável da aplicação não encontrado em: %s", APP_EXECUTABLE_PATH)
            return
        logging.info("Iniciando a aplicação: %s", APP_EXECUTABLE_PATH)
        try:
            subprocess.Popen([APP_EXECUTABLE_PATH])
        except OSError as e:
            logging.error("Erro ao iniciar a aplicação: %s", e)


def main():
    """Função principal que inicializa e executa o Updater."""
    setup_logging('updater.log', log_to_console=True)
    logging.info("Updater Gráfico iniciado.")

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    mode = 'check'
    if len(sys.argv) > 1 and sys.argv[1] == '--apply':
        mode = 'apply'

    window = UpdaterWindow(mode=mode)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
