"""
Formulário de Autenticação.

Este módulo implementa uma interface gráfica para autenticação de usuários no sistema.
As funcionalidades incluem login de usuários existentes e criação de novos usuários,
com a possibilidade de definir permissões administrativas. A interface é construída
com a biblioteca PySide6, utilizando o módulo globals para variáveis globais e o
módulo funcoes para operações auxiliares. O banco de dados é gerenciado com SQLAlchemy.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.exc import SQLAlchemyError

from src.components.barra_titulo import BarraTitulo
from src.config import globals as g
from src.models.models import Usuario
from src.utils.banco_dados import get_session
from src.utils.estilo import aplicar_estilo_botao, obter_tema_atual
from src.utils.janelas import Janela
from src.utils.usuarios import login, novo_usuario
from src.utils.utilitarios import aplicar_medida_borda_espaco, show_error

# Constantes para configuração da interface
JANELA_LARGURA = 200
JANELA_ALTURA_LOGIN = 160
JANELA_ALTURA_CADASTRO = 180


def _configurar_janela_base(root):
    """Configura a janela base do formulário de autenticação."""
    if g.AUTEN_FORM:
        g.AUTEN_FORM.close()
        g.AUTEN_FORM = None

    g.AUTEN_FORM = QDialog(root)
    g.AUTEN_FORM.setFixedSize(JANELA_LARGURA, JANELA_ALTURA_LOGIN)
    g.AUTEN_FORM.setModal(True)
    g.AUTEN_FORM.setWindowFlags(
        Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window
    )

    def close_event(event):
        Janela.estado_janelas(True)
        event.accept()

    g.AUTEN_FORM.closeEvent = close_event


def _criar_layout_principal():
    """Cria o layout principal da janela."""
    vlayout = QVBoxLayout(g.AUTEN_FORM)
    aplicar_medida_borda_espaco(vlayout, 5)
    return vlayout


def _criar_barra_titulo(vlayout):
    """Cria e configura a barra de título."""
    barra = BarraTitulo(g.AUTEN_FORM, tema=obter_tema_atual())

    if g.LOGIN:
        barra.titulo.setText("Login")
    else:
        barra.titulo.setText("Novo Usuário")

    vlayout.addWidget(barra)
    return barra


def _criar_campos_usuario_senha(main_layout):
    """Cria os campos de usuário e senha."""
    main_layout.addWidget(QLabel("Usuário:"), 0, 0)
    g.USUARIO_ENTRY = QLineEdit()
    main_layout.addWidget(g.USUARIO_ENTRY, 0, 1)

    main_layout.addWidget(QLabel("Senha:"), 1, 0)
    g.SENHA_ENTRY = QLineEdit()
    g.SENHA_ENTRY.setEchoMode(QLineEdit.EchoMode.Password)
    main_layout.addWidget(g.SENHA_ENTRY, 1, 1)


def _verificar_admin_existente():
    """Verifica se já existe um usuário administrador."""
    try:
        with get_session() as session:
            return session.query(Usuario).filter(Usuario.role == "admin").first()
    except SQLAlchemyError as e:
        show_error("Erro de DB", f"Não foi possível verificar admin: {e}")
        return (
            True  # Assume que admin existe para prevenir novos admins em caso de erro
        )


def _configurar_modo_login(main_layout):
    """Configura o formulário para modo login."""
    g.AUTEN_FORM.setWindowTitle("Login")
    login_btn = QPushButton("🔐 Login")
    aplicar_estilo_botao(login_btn, "verde")
    login_btn.clicked.connect(login)
    main_layout.addWidget(login_btn, 3, 0, 1, 2)


def _configurar_checkbox_admin(main_layout):
    """Configura o checkbox de administrador."""
    g.AUTEN_FORM.setFixedSize(JANELA_LARGURA, JANELA_ALTURA_CADASTRO)
    main_layout.addWidget(QLabel("Admin:"), 2, 0)
    admin_checkbox = QCheckBox()

    def on_admin_checkbox_changed(checked):
        g.ADMIN_VAR = "admin" if checked else "viewer"

    admin_checkbox.stateChanged.connect(on_admin_checkbox_changed)
    main_layout.addWidget(admin_checkbox, 2, 1)


def _configurar_modo_novo_usuario(main_layout):
    """Configura o formulário para modo novo usuário."""
    admin_existente = _verificar_admin_existente()

    if not admin_existente:
        _configurar_checkbox_admin(main_layout)
    else:
        g.ADMIN_VAR = "viewer"

    g.AUTEN_FORM.setWindowTitle("Novo Usuário")
    save_btn = QPushButton("💾 Salvar")
    aplicar_estilo_botao(save_btn, "azul")
    save_btn.clicked.connect(novo_usuario)
    main_layout.addWidget(save_btn, 3, 0, 1, 2)


def _criar_conteudo_principal(vlayout):
    """Cria o widget de conteúdo principal."""
    conteudo = QWidget()
    main_layout = QGridLayout(conteudo)

    _criar_campos_usuario_senha(main_layout)

    g.ADMIN_VAR = "viewer"

    if g.LOGIN:
        _configurar_modo_login(main_layout)
    else:
        _configurar_modo_novo_usuario(main_layout)

    conteudo.setLayout(main_layout)
    vlayout.addWidget(conteudo)


def _finalizar_configuracao():
    """Finaliza a configuração da janela."""
    Janela.posicionar_janela(g.AUTEN_FORM, "centro")
    g.AUTEN_FORM.show()
    g.AUTEN_FORM.raise_()
    g.AUTEN_FORM.activateWindow()

    if g.USUARIO_ENTRY:
        g.USUARIO_ENTRY.setFocus()


def main(root):
    """Função principal que cria a janela de autenticação."""
    _configurar_janela_base(root)
    vlayout = _criar_layout_principal()
    _criar_barra_titulo(vlayout)
    _criar_conteudo_principal(vlayout)
    _finalizar_configuracao()
