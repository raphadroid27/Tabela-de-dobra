"""
# Formulário de Gerenciamento de Usuários
# Este módulo implementa uma interface gráfica para gerenciar usuários do sistema.
# As funcionalidades incluem redefinir senhas, alterar permissões e excluir usuários.
# A interface é construída com a biblioteca PySide6, utilizando o módulo globals
# para variáveis globais e o módulo funcoes para operações relacionadas ao banco de dados.
"""
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QPushButton, QTreeWidget, QTreeWidgetItem, QFrame, QGroupBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from src.utils.janelas import (aplicar_no_topo, posicionar_janela)
from src.utils.interface import (listar, limpar_busca)
from src.utils.utilitarios import obter_caminho_icone
from src.utils.operacoes_crud import buscar
from src.utils.usuarios import (tem_permissao,
                                tornar_editor,
                                resetar_senha,
                                excluir_usuario
                                )
from src.config import globals as g


def main(root):
    """
    Função principal para gerenciar usuários.
    Inicializa a interface gráfica para edição, exclusão e gerenciamento de permissões.
    """
    # Verificar se o usuário é administrador
    if not tem_permissao('usuario', 'admin'):
        return

    if g.USUAR_FORM is not None:
        g.USUAR_FORM.close()

    g.USUAR_FORM = QDialog(root)
    g.USUAR_FORM.setWindowTitle("Editar/Excluir Usuário")
    g.USUAR_FORM.setFixedSize(300, 280)

    # Define o ícone
    icone_path = obter_caminho_icone()
    g.USUAR_FORM.setWindowIcon(QIcon(icone_path))

    aplicar_no_topo(g.USUAR_FORM)
    posicionar_janela(g.USUAR_FORM, 'centro')

    main_layout = QGridLayout()
    g.USUAR_FORM.setLayout(main_layout)

    # Frame de busca
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
    limpar_btn.setStyleSheet("""
        QPushButton {
            background-color: #ffd93d;
            color: #333;
            border: none;
            padding: 4px 8px;
            font-weight: bold;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #ffcc02;
        }
        QPushButton:pressed {
            background-color: #e6b800;
        }
    """)
    limpar_btn.clicked.connect(lambda: limpar_busca('usuario'))
    busca_layout.addWidget(limpar_btn, 0, 2)

    main_layout.addWidget(frame_busca, 0, 0, 1, 3)

    # TreeWidget para listar usuários
    g.LIST_USUARIO = QTreeWidget()
    g.LIST_USUARIO.setHeaderLabels(["Id", "Nome", "Permissões"])
    g.LIST_USUARIO.setColumnHidden(0, True)  # Esconde a coluna Id
    g.LIST_USUARIO.setColumnWidth(1, 150)
    g.LIST_USUARIO.setColumnWidth(2, 100)

    main_layout.addWidget(g.LIST_USUARIO, 1, 0, 1, 3)

    # Botões de ação
    tornar_editor_btn = QPushButton("👤 Tornar Editor")
    tornar_editor_btn.setStyleSheet("""
        QPushButton {
            background-color: #4caf50;
            color: white;
            border: none;
            padding: 4px 8px;
            font-weight: bold;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #45a049;
        }
        QPushButton:pressed {
            background-color: #3d8b40;
        }
    """)
    tornar_editor_btn.clicked.connect(tornar_editor)
    main_layout.addWidget(tornar_editor_btn, 2, 0)

    resetar_senha_btn = QPushButton("🔄 Resetar Senha")
    resetar_senha_btn.setStyleSheet("""
        QPushButton {
            background-color: #ffd93d;
            color: #333;
            border: none;
            padding: 4px 8px;
            font-weight: bold;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #ffcc02;
        }
        QPushButton:pressed {
            background-color: #e6b800;
        }
    """)
    resetar_senha_btn.clicked.connect(resetar_senha)
    main_layout.addWidget(resetar_senha_btn, 2, 1)

    excluir_btn = QPushButton("🗑️ Excluir")
    excluir_btn.setStyleSheet("""
        QPushButton {
            background-color: #ff6b6b;
            color: white;
            border: none;
            padding: 4px 8px;
            font-weight: bold;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #ff5252;
        }
        QPushButton:pressed {
            background-color: #e53935;
        }
    """)
    excluir_btn.clicked.connect(excluir_usuario)
    main_layout.addWidget(excluir_btn, 2, 2)

    listar('usuario')


if __name__ == "__main__":
    main(None)
