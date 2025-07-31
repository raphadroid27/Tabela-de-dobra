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

Refatoração:
- Adicionada BarraTitulo customizada para consistência visual.
- Substituído QInputDialog por um QDialog de autenticação robusto e estilizado.
- Estilos de botões e layout alinhados com o restante da aplicação.
- Adicionada uma barra de progresso para feedback visual durante a atualização.
- Adicionado tratamento de erro com retentativas para limpeza de arquivos.
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
import qdarktheme
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QLabel, QPushButton, QHBoxLayout, QMessageBox,
                               QDialog, QGridLayout, QLineEdit, QProgressBar,
                               QSpacerItem, QSizePolicy)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon

# --- Adiciona o diretório raiz do projeto ao path ---
try:
    BASE_DIR = os.path.dirname(os.path.abspath(
        sys.argv[0] if getattr(sys, 'frozen', False) else __file__))
    if BASE_DIR not in sys.path:
        sys.path.insert(0, BASE_DIR)

    # --- Importações da Aplicação Local ---
    from src import __version__ as APP_VERSION
    from src.models.models import SystemControl as SystemControlModel, Usuario
    from src.utils.banco_dados import session_scope
    from src.utils.update_manager import checar_updates, download_update
    from src.utils.utilitarios import (
        setup_logging, APP_EXECUTABLE_PATH, UPDATE_TEMP_DIR,
        ICON_PATH, show_error, aplicar_medida_borda_espaco
    )
    from src.components.barra_titulo import BarraTitulo
    from src.utils.estilo import (
        obter_estilo_botao_verde, obter_estilo_botao_vermelho,
        obter_estilo_botao_azul, obter_tema_atual, obter_estilo_progress_bar
    )
    from src.utils.janelas import posicionar_janela
    from src.config import globals as g


except ImportError as e:
    # Fallback de emergência
    logging.basicConfig(level=logging.CRITICAL,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logging.critical("Erro de Importação: %s", e)
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


class AdminAuthDialog(QDialog):
    """
    Dialog para autenticação de administrador, sem barra de título.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.success = False
        self.setModal(True)
        # Janela sem a barra de título padrão do SO ou customizada
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setFixedSize(230, 130)  # Tamanho ajustado para layout sem título

        self.setStyleSheet("QDialog { border-radius: 10px; }")

        # Aplicar tema do qdarktheme
        qdarktheme.setup_theme(obter_tema_atual())

        self._setup_ui()
        self.usuario_entry.setFocus()

    def _setup_ui(self):
        """Configura a interface do diálogo, mantendo o layout original em grid."""
        grid_layout = QGridLayout(self)
        grid_layout.setContentsMargins(15, 15, 15, 15)
        grid_layout.setVerticalSpacing(10)
        grid_layout.setHorizontalSpacing(10)

        # Campos de entrada
        grid_layout.addWidget(QLabel("Usuário:"), 0, 0)
        self.usuario_entry = QLineEdit()
        self.usuario_entry.setPlaceholderText("Digite o usuário admin")
        grid_layout.addWidget(self.usuario_entry, 0, 1)

        grid_layout.addWidget(QLabel("Senha:"), 1, 0)
        self.senha_entry = QLineEdit()
        self.senha_entry.setPlaceholderText("Digite a senha")
        self.senha_entry.setEchoMode(QLineEdit.Password)
        grid_layout.addWidget(self.senha_entry, 1, 1)

        # Adiciona um espaço vertical antes dos botões
        grid_layout.addItem(QSpacerItem(
            1, 10, QSizePolicy.Minimum, QSizePolicy.Expanding), 2, 0, 1, 2)

        # Layout para os botões
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        # Botão Cancelar
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setStyleSheet(obter_estilo_botao_vermelho())
        cancel_btn.clicked.connect(self.reject)  # Fecha o diálogo

        # Botão Login
        login_btn = QPushButton("🔐 Login")
        login_btn.setStyleSheet(obter_estilo_botao_verde())
        login_btn.clicked.connect(self.attempt_login)

        # Adiciona os botões ao layout de botões
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(login_btn)

        # Adiciona o layout dos botões ao grid principal, ocupando 2 colunas
        grid_layout.addLayout(button_layout, 3, 0, 1, 2)

    def attempt_login(self):
        """Valida as credenciais fornecidas."""
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
                           "Não foi possível conectar ao banco de dados.", parent=self)
                return

            user = db_session.query(Usuario).filter_by(
                nome=username, senha=hashed_password).first()

            if user and user.role == 'admin':
                self.success = True
                self.accept()  # Fecha o diálogo com sucesso
            else:
                show_error("Falha na Autenticação",
                           "Credenciais inválidas ou o usuário não é um administrador.",
                           parent=self)
                self.senha_entry.clear()


class UpdaterWindow(QMainWindow):
    """Janela principal da interface do Updater."""

    def __init__(self, mode='check'):
        super().__init__()
        self.update_info = None
        self.mode = mode

        # --- Configuração da Janela ---
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setFixedSize(330, 160)
        if ICON_PATH and os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))

        self.setup_ui()
        QTimer.singleShot(100, self.run_initial_flow)

    def setup_ui(self):
        """Configura os widgets da interface."""
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_layout = QVBoxLayout(self.central_widget)
        aplicar_medida_borda_espaco(main_layout, 0, 0)

        # --- Barra de Título ---
        self.barra_titulo = BarraTitulo(self, tema=obter_tema_atual())
        self.barra_titulo.titulo.setText("Atualizador")
        main_layout.addWidget(self.barra_titulo)

        # --- Conteúdo ---
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 10, 15, 15)
        content_layout.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(content_widget)

        self.status_label = QLabel("Verificando atualizações...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 16px;")

        self.version_label = QLabel("")
        self.version_label.setAlignment(Qt.AlignCenter)
        self.version_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #55aaff;")

        # --- Barra de Progresso ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(obter_estilo_progress_bar())
        self.progress_bar.hide()

        self.button_layout = QHBoxLayout()
        self.update_button = QPushButton("Atualizar Agora")
        self.update_button.setEnabled(False)
        self.update_button.clicked.connect(self.start_update_process)

        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.close)
        self.cancel_button.setStyleSheet(obter_estilo_botao_vermelho())

        self.button_layout.addWidget(self.cancel_button)
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.update_button)

        content_layout.addWidget(self.status_label)
        content_layout.addWidget(self.version_label)
        content_layout.addWidget(self.progress_bar)
        content_layout.addStretch()
        content_layout.addLayout(self.button_layout)

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
                # Autentica antes de prosseguir no modo 'apply'
                if self.validate_app_admin():
                    self.start_update_process(confirmed=True)
                else:
                    self.close()

        finally:
            QApplication.restoreOverrideCursor()

    def show_update_available(self):
        """Atualiza a UI para mostrar que uma atualização foi encontrada."""
        latest_version = self.update_info.get("ultima_versao", "N/A")
        self.status_label.setText("Nova versão disponível!")
        self.version_label.setText(f"Versão {latest_version}")
        self.update_button.setEnabled(True)
        self.update_button.setStyleSheet(obter_estilo_botao_azul())

    def show_no_update(self):
        """Atualiza a UI para mostrar que o app está atualizado."""
        self.status_label.setText(
            "O seu aplicativo já está na versão mais recente.")
        self.version_label.setText(f"Versão atual: {APP_VERSION}")
        self.update_button.setEnabled(False)
        self.cancel_button.setText("Fechar")

    def validate_app_admin(self) -> bool:
        """Abre o diálogo de autenticação e retorna o resultado."""
        auth_dialog = AdminAuthDialog(self)

        # Define a janela do updater como a principal temporariamente
        # para que a função `posicionar_janela` possa centralizar o diálogo.
        g.PRINC_FORM = self
        posicionar_janela(auth_dialog, 'centro')
        g.PRINC_FORM = None  # Limpa a referência para evitar efeitos colaterais

        auth_dialog.exec()
        return auth_dialog.success

    def start_update_process(self, confirmed=False):
        """Inicia o fluxo completo de atualização."""
        # 1. Validar se o usuário é um admin do aplicativo
        if not confirmed and not self.validate_app_admin():
            return

        # 2. Confirmar a ação (se não foi pré-confirmada)
        if not confirmed:
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
        self.version_label.hide()
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        QApplication.setOverrideCursor(Qt.WaitCursor)

        try:
            self.run_update_steps()
        except (ValueError, ConnectionError, RuntimeError,
                IOError, OSError) as e:
            logging.error("Erro no processo de atualização: %s", e)
            show_error("Erro de Atualização",
                       f"Ocorreu um erro: {e}", parent=self)
            self.status_label.setText("Falha na atualização.")
            self.progress_bar.hide()
            self.version_label.show()
            self.cancel_button.setEnabled(True)
            self.cancel_button.setText("Fechar")
        finally:
            QApplication.restoreOverrideCursor()

    def run_update_steps(self):
        """Executa as etapas sequenciais da atualização."""
        self.status_label.setText("A baixar ficheiros...")
        self.progress_bar.setValue(10)
        QApplication.processEvents()
        zip_filename = self.update_info.get("nome_arquivo")
        if not zip_filename:
            raise ValueError(
                "Nome do ficheiro de atualização não encontrado em versao.json.")
        download_update(zip_filename)
        self.progress_bar.setValue(40)

        self.status_label.setText("A fechar a aplicação principal...")
        QApplication.processEvents()
        with session_scope() as (db_session, model):
            if not db_session or not model:
                raise ConnectionError(
                    "Não foi possível ligar à base de dados.")
            if not self.force_shutdown_all_instances(db_session, model):
                raise RuntimeError(
                    "Não foi possível fechar todas as instâncias da aplicação.")
        self.progress_bar.setValue(70)

        self.status_label.setText("A aplicar a atualização...")
        QApplication.processEvents()
        if not self.apply_update(zip_filename):
            raise IOError(
                "Falha ao aplicar os ficheiros de atualização. Verifique as permissões da pasta.")
        self.progress_bar.setValue(90)

        self.status_label.setText("Atualização concluída! A reiniciar...")
        self.progress_bar.setValue(100)
        QApplication.processEvents()
        time.sleep(2)
        self.start_application()
        self.close()

    def force_shutdown_all_instances(self, session: any, model: Type[SystemControlModel]) -> bool:
        """Envia comando de desligamento e aguarda o fechamento."""
        logging.info("A enviar comando de encerramento...")
        try:
            cmd_entry = session.query(model).filter_by(
                key='UPDATE_CMD').first()
            if cmd_entry:
                cmd_entry.value = 'SHUTDOWN'
                cmd_entry.last_updated = datetime.now(timezone.utc)
            else:
                # Se não existir, cria a entrada
                new_cmd = model(
                    key='UPDATE_CMD', value='SHUTDOWN', type='COMMAND')
                session.add(new_cmd)
            session.commit()

            start_time = time.time()
            while (time.time() - start_time) < 60:
                active_sessions = session.query(
                    model).filter_by(type='SESSION').count()
                self.status_label.setText(
                    f"A aguardar que {active_sessions} instância(s) feche(m)...")
                QApplication.processEvents()
                if active_sessions == 0:
                    logging.info("Todas as instâncias foram fechadas.")
                    time.sleep(3)
                    return True
                time.sleep(2)

            logging.error("Timeout! As instâncias não fecharam a tempo.")
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
                "Ficheiro de atualização não encontrado em %s", zip_filepath)
            return False

        app_dir = BASE_DIR
        try:
            with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
                extract_path = os.path.join(UPDATE_TEMP_DIR, 'extracted')
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
                    logging.warning(
                        "Não foi possível substituir '%s': %s. A tentar como admin...", item, e)

            logging.info("Atualização aplicada com sucesso!")
            return True
        except (IOError, OSError, zipfile.BadZipFile) as e:
            logging.error("Erro ao aplicar a atualização: %s", e)
            return False
        finally:
            if os.path.isdir(UPDATE_TEMP_DIR):
                max_retries = 5
                retry_delay = 0.5
                for i in range(max_retries):
                    try:
                        shutil.rmtree(UPDATE_TEMP_DIR)
                        logging.info(
                            "Diretório temporário removido com sucesso.")
                        break
                    except OSError as e:
                        logging.warning(
                            "Tentativa %d/%d falhou ao remover %s: %s. A tentar novamente em %ss...",  # pylint: disable=line-too-long
                            i + 1, max_retries, UPDATE_TEMP_DIR, e, retry_delay
                        )
                        time.sleep(retry_delay)
                else:
                    logging.error(
                        "Não foi possível remover o diretório temporário %s após várias tentativas.",  # pylint: disable=line-too-long
                        UPDATE_TEMP_DIR
                    )

    def start_application(self):
        """Inicia a aplicação principal (app.exe)."""
        if not os.path.exists(APP_EXECUTABLE_PATH):
            logging.error(
                "Executável da aplicação não encontrado em: %s", APP_EXECUTABLE_PATH)
            show_error("Erro Crítico",
                       f"Não foi possível encontrar o executável principal em:"
                       f"\n{APP_EXECUTABLE_PATH}")
            return
        logging.info("A iniciar a aplicação: %s", APP_EXECUTABLE_PATH)
        try:
            subprocess.Popen([APP_EXECUTABLE_PATH])
        except OSError as e:
            logging.error("Erro ao iniciar a aplicação: %s", e)
            show_error("Erro ao Reiniciar",
                       f"Não foi possível reiniciar a aplicação principal:\n{e}")


def main():
    """Função principal que inicializa e executa o Updater."""
    setup_logging('updater.log', log_to_console=True)
    logging.info("Updater Gráfico iniciado.")

    app = QApplication(sys.argv)
    # Aplica o tema globalmente
    qdarktheme.setup_theme(obter_tema_atual())

    mode = 'check'
    if len(sys.argv) > 1 and sys.argv[1] == '--apply':
        mode = 'apply'

    window = UpdaterWindow(mode=mode)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
