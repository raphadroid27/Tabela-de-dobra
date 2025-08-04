"""
# Formulário "Sobre"
# Este módulo implementa a janela "Sobre" do aplicativo.
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout, QWidget

from src import __version__
from src.components.barra_titulo import BarraTitulo
from src.config import globals as g
from src.utils.estilo import obter_tema_atual

# CORREÇÃO: Importa apenas a classe Janela.
from src.utils.janelas import Janela
from src.utils.utilitarios import ICON_PATH, aplicar_medida_borda_espaco


def main(root: Optional[QWidget]) -> None:
    """
    Função principal que cria a janela "Sobre" com barra de título customizada.
    """
    if hasattr(g, "SOBRE_FORM") and g.SOBRE_FORM is not None:
        g.SOBRE_FORM.close()

    sobre_form = QDialog(root)
    g.SOBRE_FORM = sobre_form
    sobre_form.setWindowTitle("Sobre")
    sobre_form.setFixedSize(300, 210)
    sobre_form.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)

    sobre_form.setWindowIcon(QIcon(ICON_PATH))

    # CORREÇÃO: Chamadas explícitas através da classe Janela.
    Janela.aplicar_no_topo(sobre_form)
    Janela.posicionar_janela(sobre_form, "centro")

    # Layout principal vertical: barra de título + conteúdo
    layout = QVBoxLayout(sobre_form)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    # Barra de título customizada
    barra = BarraTitulo(sobre_form, tema=obter_tema_atual())
    barra.titulo.setText("Sobre")
    layout.addWidget(barra)

    # Widget de conteúdo principal
    conteudo = QWidget()
    conteudo_layout = QVBoxLayout(conteudo)
    aplicar_medida_borda_espaco(conteudo_layout, 10, 10)

    # Título
    label_titulo = QLabel("Cálculo de Dobra")
    font_titulo = QFont("Arial", 16)
    font_titulo.setBold(True)
    label_titulo.setFont(font_titulo)
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

    sobre_form.show()


if __name__ == "__main__":
    main(None)
