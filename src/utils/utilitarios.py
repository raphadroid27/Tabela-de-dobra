# -*- coding: utf-8 -*-
"""
Funções utilitárias genéricas para o aplicativo de cálculo de dobras.
"""
import logging
import logging.handlers
import os
import sys

from PySide6.QtWidgets import (QInputDialog, QLineEdit, QMessageBox)


def obter_caminho_icone():
    """
    Retorna o caminho correto para o arquivo de ícone.

    Considera o modo de execução (normal ou empacotado com PyInstaller)
    para encontrar a pasta 'assets'.
    """
    if getattr(sys, 'frozen', False):
        # Em modo 'congelado', a base é o diretório do executável
        base_path = os.path.dirname(sys.executable)
    else:
        # Em modo de script, sobe dois níveis de src/utils para a raiz
        base_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), '..', '..'))

    return os.path.join(base_path, "assets", "icone_2.ico")


def aplicar_medida_borda_espaco(layout_ou_widget, margem=5, espaco=5):
    """
    Aplica margens e espaçamento a um layout ou widget.
    """
    if hasattr(layout_ou_widget, 'setContentsMargins'):
        layout_ou_widget.setContentsMargins(margem, margem, margem, margem)
    if hasattr(layout_ou_widget, 'setSpacing'):
        layout_ou_widget.setSpacing(espaco)
    elif hasattr(layout_ou_widget, 'layout') and layout_ou_widget.layout():
        layout = layout_ou_widget.layout()
        if hasattr(layout, 'setContentsMargins'):
            layout.setContentsMargins(margem, margem, margem, margem)
        if hasattr(layout, 'setSpacing'):
            layout.setSpacing(espaco)


def ask_string(title, prompt, parent=None):
    """Pede uma string usando QInputDialog."""
    text, ok = QInputDialog.getText(
        parent, title, prompt, QLineEdit.Normal)
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

    A lógica foi revisada para garantir que o diretório 'logs' seja criado
    corretamente no diretório base da aplicação, tanto em modo de script
    quanto em modo 'congelado' (executável).

    Args:
        log_filename (str): O nome do arquivo de log (ex: 'app.log').
        log_to_console (bool): Se True, os logs também serão enviados para a
                               saída padrão.
    """
    try:
        if getattr(sys, 'frozen', False):
            # Modo 'congelado' (executável): o diretório base é onde o executável está.
            base_dir = os.path.dirname(sys.executable)
        else:
            # Modo de script: __file__ está em src/utils, então subimos dois níveis.
            base_dir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), '..', '..'))

        log_dir = os.path.join(base_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)

        log_filepath = os.path.join(log_dir, log_filename)

        log_format = logging.Formatter(
            '%(asctime)s - [%(levelname)s] - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        # Limpa handlers antigos para evitar duplicação de logs
        if logger.hasHandlers():
            logger.handlers.clear()

        # Handler para arquivo, com rotação (aumentado para 5MB)
        file_handler = logging.handlers.RotatingFileHandler(
            log_filepath, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8'
        )
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)

        # Handler para console, se habilitado
        if log_to_console:
            stream_handler = logging.StreamHandler(sys.stdout)
            stream_handler.setFormatter(log_format)
            logger.addHandler(stream_handler)

        logging.info("="*50)
        logging.info(
            "Logging configurado. Arquivo de log em: %s", log_filepath)

    except (OSError, IOError) as e:
        # Fallback para o console se a configuração do arquivo falhar
        print(
            f"ERRO CRÍTICO: Não foi possível configurar o logging em arquivo: {e}")
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        logging.error(
            "Falha ao inicializar o handler de arquivo de log.", exc_info=True)
