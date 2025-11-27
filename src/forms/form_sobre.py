"""Formulário "Sobre".

Este módulo implementa a janela "Sobre" do aplicativo.
"""

import sys
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QDialog, QLabel, QVBoxLayout, QWidget

from src import __version__
from src.forms.common.ui_helpers import configurar_dialogo_padrao
from src.utils.janelas import Janela
from src.utils.utilitarios import ICON_PATH, aplicar_medida_borda_espaco


def main(root: Optional[QWidget]) -> None:
    """Create and display the About dialog with custom title bar."""
    sobre_form = QDialog(root)
    sobre_form.setWindowTitle("Sobre")
    sobre_form.setFixedSize(280, 190)
    configurar_dialogo_padrao(sobre_form, ICON_PATH)
    sobre_form.setModal(True)
    sobre_form.setWindowFlags(Qt.WindowType.WindowCloseButtonHint)

    Janela.posicionar_janela(sobre_form, "centro")

    # Layout principal vertical: barra de título + conteúdo
    layout = QVBoxLayout(sobre_form)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    # Widget de conteúdo principal
    conteudo = QWidget()
    conteudo_layout = QVBoxLayout(conteudo)
    aplicar_medida_borda_espaco(conteudo_layout, 10, 10)

    # Título
    label_titulo = QLabel("Calculadora de Dobra")
    label_titulo.setObjectName("label_titulo_h4")
    label_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
    conteudo_layout.addWidget(label_titulo)

    # Versão
    label_versao = QLabel(f"Versão: {__version__}")
    font_normal = QFont("Arial", 12)
    label_versao.setFont(font_normal)
    label_versao.setAlignment(Qt.AlignmentFlag.AlignCenter)
    conteudo_layout.addWidget(label_versao)

    # Autor
    label_autor = QLabel("Autor: raphadroid27")
    label_autor.setFont(font_normal)
    label_autor.setAlignment(Qt.AlignmentFlag.AlignCenter)
    conteudo_layout.addWidget(label_autor)

    # Descrição
    label_desc = QLabel("Aplicativo para cálculo de dobras em\nchapas metálicas.")
    label_desc.setObjectName("label_texto")
    label_desc.setFont(font_normal)
    label_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
    conteudo_layout.addWidget(label_desc)

    # Link para o GitHub
    label_link = QLabel(
        '<a href="https://github.com/raphadroid27/Tabela-de-dobra">Repositório no GitHub</a>'
    )
    label_link.setFont(font_normal)
    label_link.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label_link.setOpenExternalLinks(True)
    conteudo_layout.addWidget(label_link)

    conteudo.setLayout(conteudo_layout)
    layout.addWidget(conteudo)

    sobre_form.exec()
    return sobre_form


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main(None)
    sys.exit(app.exec())
