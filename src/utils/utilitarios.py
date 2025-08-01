# -*- coding: utf-8 -*-
"""
Funções e constantes utilitárias genéricas para a aplicação.

Este módulo centraliza a gestão de caminhos, a configuração de logs e as
funções de diálogo com o usuário (QMessageBox, QInputDialog).
"""

import logging
import logging.handlers
import os
import sys

from PySide6.QtWidgets import QInputDialog, QLineEdit, QMessageBox

from src.config import globals as g

# --- 1. LÓGICA CENTRALIZADA DE CAMINHOS ---


def obter_dir_base() -> str:
    """
    Retorna o diretório base da aplicação de forma consistente.

    Verifica se a aplicação está rodando como um script ou como um executável
    "congelado" para determinar o caminho raiz correto.

    Returns:
        str: O caminho absoluto para o diretório raiz da aplicação.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    # Em modo de script, assume-se que este arquivo está em 'src/utils',
    # então o diretório base está dois níveis acima.
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def obter_dir_icone():
    """
    Retorna o caminho correto para o arquivo de ícone,
    considerando o modo de execução (normal ou empacotado).
    """
    if getattr(sys, "frozen", False):  # Verifica se está empacotado
        base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    else:
        base_path = os.path.abspath(".")  # Diretório atual no modo normal

    return os.path.join(base_path, "assets", "icone_2.ico")


# --- Constantes de Caminhos Globais ---


BASE_DIR = obter_dir_base()

# Diretório de banco de dados
DATABASE_DIR = os.path.join(BASE_DIR, "database")
DB_PATH = os.path.join(DATABASE_DIR, "tabela_de_dobra.db")

# Ícone da aplicação
ICON_PATH = obter_dir_icone()

# Diretório de logs
LOG_DIR = os.path.join(BASE_DIR, "logs")

# Diretórios e arquivos de atualização
UPDATES_DIR = os.path.join(BASE_DIR, "updates")
UPDATE_TEMP_DIR = os.path.join(BASE_DIR, "update_temp")
VERSION_FILE_PATH = os.path.join(UPDATES_DIR, "versao.json")

# Arquivo executável da aplicação principal
APP_EXECUTABLE_NAME = "Cálculo de Dobra.exe"
APP_EXECUTABLE_PATH = os.path.join(BASE_DIR, APP_EXECUTABLE_NAME)

# Arquivos de configuração do usuário
DOCUMENTS_DIR = os.path.join(os.environ["USERPROFILE"], "Documents")
CONFIG_DIR = os.path.join(DOCUMENTS_DIR, "Cálculo de Dobra")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


def ensure_dirs_exist():
    """
    Garante que todos os diretórios essenciais para a aplicação existam.
    """
    os.makedirs(DATABASE_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(CONFIG_DIR, exist_ok=True)


# Garante a criação dos diretórios na importação do módulo.
ensure_dirs_exist()


# --- 2. FUNÇÕES UTILITÁRIAS ---
def aplicar_medida_borda_espaco(layout_ou_widget, margem=5, espaco=5):
    """Aplica margens e espaçamento a um layout ou widget."""
    if hasattr(layout_ou_widget, "setContentsMargins"):
        layout_ou_widget.setContentsMargins(margem, margem, margem, margem)
    if hasattr(layout_ou_widget, "setSpacing"):
        layout_ou_widget.setSpacing(espaco)
    elif hasattr(layout_ou_widget, "layout") and layout_ou_widget.layout():
        layout = layout_ou_widget.layout()
        if hasattr(layout, "setContentsMargins"):
            layout.setContentsMargins(margem, margem, margem, margem)
        if hasattr(layout, "setSpacing"):
            layout.setSpacing(espaco)


def tem_configuracao_dobras_valida():
    """Verifica se as configurações de dobras estão disponíveis.

    Returns:
        bool: True se VALORES_W e N estão definidos em globals
    """
    return hasattr(g, "VALORES_W") and hasattr(g, "N")


def ask_string(title, prompt, parent=None):
    """Pede uma string usando QInputDialog."""
    text, ok = QInputDialog.getText(parent, title, prompt, QLineEdit.Normal)
    return text if ok else None


def show_error(title, message, parent=None):
    """Mostra uma mensagem de erro usando QMessageBox."""
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Critical)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec()


def show_info(title, message, parent=None):
    """Mostra uma mensagem de informação usando QMessageBox."""
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Information)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec()


def show_warning(title, message, parent=None):
    """Mostra uma mensagem de aviso usando QMessageBox."""
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec()


def ask_yes_no(title, message, parent=None):
    """Pergunta sim/não usando QMessageBox."""
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Question)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msg.setDefaultButton(QMessageBox.No)
    return msg.exec() == QMessageBox.Yes


def setup_logging(log_filename: str, log_to_console: bool = True):
    """
    Configura o logging para arquivo e, opcionalmente, para o console.
    """
    try:
        log_filepath = os.path.join(LOG_DIR, log_filename)
        log_format = logging.Formatter(
            "%(asctime)s - [%(levelname)s] - %(filename)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        if logger.hasHandlers():
            logger.handlers.clear()

        file_handler = logging.handlers.RotatingFileHandler(
            log_filepath, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)

        if log_to_console:
            stream_handler = logging.StreamHandler(sys.stdout)
            stream_handler.setFormatter(log_format)
            logger.addHandler(stream_handler)

        logging.info("=" * 50)
        logging.info("Logging configurado. Arquivo de log em: %s", log_filepath)

    except (OSError, IOError) as e:
        print(f"ERRO CRÍTICO: Não foi possível configurar o logging em arquivo: {e}")
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )
        logging.error(
            "Falha ao inicializar o handler de arquivo de log.", exc_info=True
        )
