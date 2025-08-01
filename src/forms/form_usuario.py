"""
Formulário de Gerenciamento de Usuários

Este módulo implementa uma interface gráfica para gerenciar usuários do sistema.
As funcionalidades incluem redefinir senhas, alterar permissões e excluir usuários.
A interface é construída com a biblioteca PySide6, utilizando o módulo globals
para variáveis globais e o módulo funcoes para operações relacionadas ao banco de dados.
"""

from PySide6.QtWidgets import (
    QDialog, QGridLayout, QLabel, QLineEdit, QPushButton,
    QTreeWidget, QGroupBox, QVBoxLayout, QWidget)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from src.utils.janelas import (aplicar_no_topo, posicionar_janela)
from src.utils.interface import (listar, limpar_busca)
from src.utils.utilitarios import ICON_PATH
from src.utils.controlador import buscar
from src.utils.usuarios import (
    tem_permissao, tornar_editor, resetar_senha, excluir_usuario)
from src.utils.estilo import (
    obter_estilo_botao_vermelho,
    obter_estilo_botao_amarelo,
    obter_estilo_botao_verde,
    obter_tema_atual)
from src.config import globals as g
from src.components.barra_titulo import BarraTitulo


def _verificar_permissao():
    """Verifica se o usuário tem permissão para gerenciar usuários."""
    return tem_permissao('usuario', 'admin')


def _configurar_janela_base(root):
    """Configura a janela base do formulário."""
    if g.USUAR_FORM is not None:
        g.USUAR_FORM.close()

    g.USUAR_FORM = QDialog(root)
    g.USUAR_FORM.setWindowTitle("Editar/Excluir Usuário")
    g.USUAR_FORM.setFixedSize(330, 280)
    g.USUAR_FORM.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)

    g.USUAR_FORM.setWindowIcon(QIcon(ICON_PATH))

    aplicar_no_topo(g.USUAR_FORM)
    posicionar_janela(g.USUAR_FORM, 'centro')


def _criar_layout_principal():
    """Cria o layout principal da janela."""
    vlayout = QVBoxLayout(g.USUAR_FORM)
    vlayout.setContentsMargins(0, 0, 0, 0)
    vlayout.setSpacing(0)
    return vlayout


def _criar_barra_titulo(vlayout):
    """Cria e configura a barra de título."""
    barra = BarraTitulo(g.USUAR_FORM, tema=obter_tema_atual())
    barra.titulo.setText("Editar/Excluir Usuário")
    vlayout.addWidget(barra)
    return barra


def _criar_widget_conteudo():
    """Cria o widget de conteúdo principal."""
    conteudo = QWidget()
    main_layout = QGridLayout(conteudo)
    return conteudo, main_layout


def _criar_frame_busca(main_layout):
    """Cria o frame de busca de usuários."""
    frame_busca = QGroupBox('Filtrar Usuários')
    busca_layout = QGridLayout()
    frame_busca.setLayout(busca_layout)

    busca_layout.addWidget(QLabel("Usuário:"), 0, 0)

    g.USUARIO_BUSCA_ENTRY = QLineEdit()
    busca_layout.addWidget(g.USUARIO_BUSCA_ENTRY, 0, 1)

    def on_text_changed():
        buscar('usuario')

    g.USUARIO_BUSCA_ENTRY.textChanged.connect(on_text_changed)

    limpar_btn = QPushButton("🧹 Limpar")
    limpar_btn.setStyleSheet(obter_estilo_botao_amarelo())
    limpar_btn.clicked.connect(lambda: limpar_busca('usuario'))
    busca_layout.addWidget(limpar_btn, 0, 2)

    main_layout.addWidget(frame_busca, 0, 0, 1, 3)


def _criar_tree_widget(main_layout):
    """Cria o TreeWidget para listar usuários."""
    g.LIST_USUARIO = QTreeWidget()
    g.LIST_USUARIO.setHeaderLabels(["Id", "Nome", "Permissões"])
    g.LIST_USUARIO.setColumnHidden(0, True)  # Esconde a coluna Id
    g.LIST_USUARIO.setColumnWidth(1, 150)
    g.LIST_USUARIO.setColumnWidth(2, 100)
    main_layout.addWidget(g.LIST_USUARIO, 1, 0, 1, 3)


def _criar_botoes_acao(main_layout):
    """Cria os botões de ação."""
    tornar_editor_btn = QPushButton("👤 Tornar Editor")
    tornar_editor_btn.setStyleSheet(obter_estilo_botao_verde())
    tornar_editor_btn.clicked.connect(tornar_editor)
    main_layout.addWidget(tornar_editor_btn, 2, 0)

    resetar_senha_btn = QPushButton("🔄 Resetar Senha")
    resetar_senha_btn.setStyleSheet(obter_estilo_botao_amarelo())
    resetar_senha_btn.clicked.connect(resetar_senha)
    main_layout.addWidget(resetar_senha_btn, 2, 1)

    excluir_btn = QPushButton("🗑️ Excluir")
    excluir_btn.setStyleSheet(obter_estilo_botao_vermelho())
    excluir_btn.clicked.connect(excluir_usuario)
    main_layout.addWidget(excluir_btn, 2, 2)


def _inicializar_listagem():
    """Inicializa a listagem de usuários."""
    listar('usuario')


def main(root):
    """
    Função principal para gerenciar usuários.
    Inicializa a interface gráfica para edição, exclusão e gerenciamento de permissões.
    """
    # Verificar se o usuário é administrador
    if not _verificar_permissao():
        return

    _configurar_janela_base(root)
    vlayout = _criar_layout_principal()
    _criar_barra_titulo(vlayout)

    conteudo, main_layout = _criar_widget_conteudo()

    _criar_frame_busca(main_layout)
    _criar_tree_widget(main_layout)
    _criar_botoes_acao(main_layout)
    _inicializar_listagem()

    conteudo.setLayout(main_layout)
    vlayout.addWidget(conteudo)


if __name__ == "__main__":
    main(None)
