"""
# Formulário de Autenticação
# Este módulo implementa uma interface gráfica para autenticação de usuários no sistema.
# As funcionalidades incluem login de usuários existentes e criação de novos usuários,
# com a possibilidade de definir permissões administrativas. A interface é construída
# com a biblioteca PySide6, utilizando o módulo globals para variáveis globais e o
# módulo funcoes para operações auxiliares. O banco de dados é gerenciado com SQLAlchemy.
"""
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QPushButton, QCheckBox, QFrame
from PySide6.QtCore import Qt
from src.utils.banco_dados import session
from src.models import Usuario
from src.utils.usuarios import login, novo_usuario
from src.utils.janelas import (desabilitar_janelas,
                               habilitar_janelas,
                               posicionar_janela
                               )
from src.config import globals as g


def main(root):
    """
    Função principal que cria a janela de autenticação.
    Se a janela já existir, ela é destruída antes de criar uma nova.
    A janela é configurada com campos para usuário e senha, e um botão para login ou
    criação de novo usuário, dependendo do estado atual do sistema.
    """

    if g.AUTEN_FORM:
        g.AUTEN_FORM.close()

    g.AUTEN_FORM = QDialog(root)
    g.AUTEN_FORM.setFixedSize(200, 120)
    g.AUTEN_FORM.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Dialog)
    g.AUTEN_FORM.setFocus()
    desabilitar_janelas()
    
    def close_event():
        habilitar_janelas()
        if g.AUTEN_FORM:
            g.AUTEN_FORM.close()
    
    g.AUTEN_FORM.closeEvent = lambda event: [close_event(), event.accept()]

    posicionar_janela(g.AUTEN_FORM, 'centro')

    main_layout = QGridLayout()
    g.AUTEN_FORM.setLayout(main_layout)

    main_layout.addWidget(QLabel("Usuário:"), 0, 0)
    g.USUARIO_ENTRY = QLineEdit()
    g.USUARIO_ENTRY.setFocus()
    main_layout.addWidget(g.USUARIO_ENTRY, 0, 1)
    
    main_layout.addWidget(QLabel("Senha:"), 1, 0)
    g.SENHA_ENTRY = QLineEdit()
    g.SENHA_ENTRY.setEchoMode(QLineEdit.Password)
    main_layout.addWidget(g.SENHA_ENTRY, 1, 1)

    admin_existente = session.query(Usuario).filter(Usuario.role == 'admin').first()

    # Para PySide6, vamos usar uma variável simples em vez de StringVar
    g.ADMIN_VAR = 'viewer'  # Valor padrão

    if g.LOGIN:
        g.AUTEN_FORM.setWindowTitle("Login")
        login_btn = QPushButton("Login")
        login_btn.setStyleSheet("background-color: lightblue;")
        login_btn.clicked.connect(login)
        main_layout.addWidget(login_btn, 3, 0, 1, 2)
    else:
        if not admin_existente:
            g.AUTEN_FORM.setFixedSize(200, 150)
            main_layout.addWidget(QLabel("Admin:"), 2, 0)
            # Checkbox para admin
            admin_checkbox = QCheckBox()
            
            def on_admin_checkbox_changed(checked):
                g.ADMIN_VAR = 'admin' if checked else 'viewer'
                
            admin_checkbox.stateChanged.connect(on_admin_checkbox_changed)
            main_layout.addWidget(admin_checkbox, 2, 1)
        else:
            # Se já existe admin, o novo usuário não pode ser admin
            g.ADMIN_VAR = 'viewer'

        g.AUTEN_FORM.setWindowTitle("Novo Usuário")
        save_btn = QPushButton("Salvar")
        save_btn.setStyleSheet("background-color: lightgreen;")
        save_btn.clicked.connect(novo_usuario)
        main_layout.addWidget(save_btn, 3, 0, 1, 2)


if __name__ == "__main__":
    main(None)
