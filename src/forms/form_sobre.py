"""
# Formulário "Sobre"
# Este módulo implementa a janela "Sobre" do aplicativo.
# Ele exibe informações como o nome do aplicativo, versão, autor,
# descrição e um link interativo para o repositório no GitHub.
# A janela é criada como uma QDialog do PySide6, centralizada na tela,
# e configurada para permanecer no topo das outras janelas.
# O link para o GitHub abre o navegador padrão ao ser clicado.
"""
try:
    from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QIcon, QFont, QCursor
except ImportError:
    # Fallback para PyQt6 se PySide6 não estiver disponível
    from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QIcon, QFont, QCursor

import webbrowser
from src import __version__
from src.config import globals as g
from src.utils.janelas import (aplicar_no_topo, posicionar_janela)
from src.utils.utilitarios import obter_caminho_icone


def main(root):
    """
    Função principal que cria a janela "Sobre".
    """
    g.SOBRE_FORM = QDialog(root)
    g.SOBRE_FORM.setWindowTitle("Sobre")
    g.SOBRE_FORM.resize(300, 210)
    g.SOBRE_FORM.setFixedSize(300, 210)
    g.SOBRE_FORM.setWindowFlags(g.SOBRE_FORM.windowFlags() | Qt.WindowStaysOnTopHint)

    # Define o ícone
    icone_path = obter_caminho_icone()
    g.SOBRE_FORM.setWindowIcon(QIcon(icone_path))

    aplicar_no_topo(g.SOBRE_FORM)
    posicionar_janela(g.SOBRE_FORM, 'centro')

    # Layout principal
    layout = QVBoxLayout(g.SOBRE_FORM)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(10)

    # Título
    label_titulo = QLabel("Cálculo de Dobra")
    font_titulo = QFont("Arial", 16)
    font_titulo.setBold(True)
    label_titulo.setFont(font_titulo)
    label_titulo.setAlignment(Qt.AlignCenter)
    layout.addWidget(label_titulo)

    # Versão
    label_versao = QLabel(f"Versão: {__version__}")
    font_normal = QFont("Arial", 12)
    label_versao.setFont(font_normal)
    label_versao.setAlignment(Qt.AlignCenter)
    layout.addWidget(label_versao)

    # Autor
    label_autor = QLabel("Autor: raphadroid27")
    label_autor.setFont(font_normal)
    label_autor.setAlignment(Qt.AlignCenter)
    layout.addWidget(label_autor)

    # Descrição
    label_descricao = QLabel("Aplicativo para cálculo de dobras.")
    label_descricao.setFont(font_normal)
    label_descricao.setAlignment(Qt.AlignCenter)
    layout.addWidget(label_descricao)

    def abrir_github():
        webbrowser.open("https://github.com/raphadroid27/Tabela-de-dobra")

    # Link GitHub
    link_github = QLabel("GitHub: raphadroid27/Tabela-de-dobra")
    link_github.setFont(font_normal)
    link_github.setAlignment(Qt.AlignCenter)
    link_github.setStyleSheet("color: blue;")
    link_github.setCursor(QCursor(Qt.PointingHandCursor))
    link_github.mousePressEvent = lambda event: abrir_github()
    layout.addWidget(link_github)

    g.SOBRE_FORM.show()


if __name__ == "__main__":
    main(None)
