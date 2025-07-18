"""
Funções utilitárias para o aplicativo de cálculo de dobras.
"""
import os
import sys
from PySide6.QtWidgets import QMessageBox, QInputDialog


def obter_caminho_icone():
    """
    Retorna o caminho correto para o arquivo de ícone, 
    considerando o modo de execução (normal ou empacotado).
    """
    if getattr(sys, 'frozen', False):  # Verifica se está empacotado
        base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    else:
        base_path = os.path.abspath(".")  # Diretório atual no modo normal

    return os.path.join(base_path, "assets", "icone_2.ico")


def ask_string(title, prompt, parent=None):
    """Pede uma string usando QInputDialog"""
    text, ok = QInputDialog.getText(
        parent, title, prompt, QInputDialog.Password)
    return text if ok else None


def show_error(title, message, parent=None):
    """Mostra uma mensagem de erro usando QMessageBox"""
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Critical)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec()


def show_info(title, message, parent=None):
    """Mostra uma mensagem de informação usando QMessageBox"""
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Information)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec()


def show_warning(title, message, parent=None):
    """Mostra uma mensagem de aviso usando QMessageBox"""
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec()


def ask_yes_no(title, message, parent=None):
    """Pergunta sim/não usando QMessageBox"""
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Question)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msg.setDefaultButton(QMessageBox.No)
    return msg.exec() == QMessageBox.Yes
