"""
# Formulário "Sobre"
# Este módulo implementa a janela "Sobre" do aplicativo.
# Ele exibe informações como o nome do aplicativo, versão, autor,
# descrição e um link interativo para o repositório no GitHub.
# A janela é criada como uma QDialog do PySide6, centralizada na tela,
# e configurada para permanecer no topo das outras janelas.
# O link para o GitHub abre o navegador padrão ao ser clicado.
"""


from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QFont
from src import __version__
from src.config import globals as g
from src.utils.janelas import (aplicar_no_topo, posicionar_janela)
from src.utils.utilitarios import obter_caminho_icone
from src.utils.interface import aplicar_medida_borda_espaco
from src.components.barra_titulo import BarraTitulo
from src.utils.estilo import obter_tema_atual


def main(root):
    """
    Função principal que cria a janela "Sobre" com barra de título customizada.
    """
    if getattr(g, 'SOBRE_FORM', None):
        g.SOBRE_FORM.close()

    g.SOBRE_FORM = QDialog(root)
    g.SOBRE_FORM.setWindowTitle("Sobre")
    g.SOBRE_FORM.resize(300, 210)
    g.SOBRE_FORM.setFixedSize(300, 210)
    # Remover barra nativa
    g.SOBRE_FORM.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)

    # Define o ícone
    icone_path = obter_caminho_icone()
    g.SOBRE_FORM.setWindowIcon(QIcon(icone_path))

    aplicar_no_topo(g.SOBRE_FORM)
    posicionar_janela(g.SOBRE_FORM, 'centro')

    # Layout principal vertical: barra de título + conteúdo
    layout = QVBoxLayout(g.SOBRE_FORM)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    # Barra de título customizada
    barra = BarraTitulo(g.SOBRE_FORM, tema=obter_tema_atual())
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
    label_titulo.setAlignment(Qt.AlignCenter)
    conteudo_layout.addWidget(label_titulo)

    # Versão
    label_versao = QLabel(f"Versão: {__version__}")
    font_normal = QFont("Arial", 12)
    label_versao.setFont(font_normal)
    label_versao.setAlignment(Qt.AlignCenter)
    conteudo_layout.addWidget(label_versao)

    # Autor
    label_autor = QLabel("Autor: raphadroid27")
    label_autor.setFont(font_normal)
    label_autor.setAlignment(Qt.AlignCenter)
    conteudo_layout.addWidget(label_autor)

    # Descrição
    label_desc = QLabel(
        "Aplicativo para cálculo de dobras em\nchapas metálicas.")
    label_desc.setFont(font_normal)
    label_desc.setAlignment(Qt.AlignCenter)
    conteudo_layout.addWidget(label_desc)

    # Link para o GitHub
    label_link = QLabel(
        '<a href="https://github.com/raphadroid27/Tabela-de-dobra">Repositório no GitHub</a>')
    label_link.setFont(font_normal)
    label_link.setAlignment(Qt.AlignCenter)
    label_link.setOpenExternalLinks(True)
    conteudo_layout.addWidget(label_link)

    conteudo.setLayout(conteudo_layout)
    layout.addWidget(conteudo)

    g.SOBRE_FORM.show()
    g.SOBRE_FORM.show()


if __name__ == "__main__":
    main(None)
