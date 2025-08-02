"""
Módulo utilitário para gerenciamento de usuários no aplicativo de cálculo de dobras.
"""

import hashlib

from PySide6.QtWidgets import QMessageBox

from src.config import globals as g
from src.models.models import Usuario
from src.utils.banco_dados import (
    session,
    tratativa_erro,
)
from src.utils.interface import listar, obter_configuracoes
from src.utils.janelas import habilitar_janelas
from src.utils.utilitarios import ask_string, show_error, show_info, show_warning


def novo_usuario():
    """
    Cria um novo usuário com o nome e senha fornecidos.
    """
    # Verificar se os widgets foram inicializados
    if g.USUARIO_ENTRY is None or g.SENHA_ENTRY is None:
        show_error("Erro", "Interface não inicializada corretamente.")
        return

    novo_usuario_nome = g.USUARIO_ENTRY.text() if g.USUARIO_ENTRY else ""
    novo_usuario_senha = g.SENHA_ENTRY.text() if g.SENHA_ENTRY else ""
    senha_hash = hashlib.sha256(novo_usuario_senha.encode()).hexdigest()

    if novo_usuario_nome == "" or novo_usuario_senha == "":
        show_error("Erro", "Preencha todos os campos.")
        return

    # Verificar se o usuário já existe
    usuario_obj = session.query(Usuario).filter_by(nome=novo_usuario_nome).first()
    if usuario_obj:
        show_error("Erro", "Usuário já existente.")
        return

    if g.ADMIN_VAR is None:
        show_error("Erro", "Variável de administrador não inicializada.")
        return

    admin_value = g.ADMIN_VAR if g.ADMIN_VAR else "viewer"
    usuario = Usuario(nome=novo_usuario_nome, senha=senha_hash, role=admin_value)
    session.add(usuario)

    # Usar tratativa_erro para tratar erros e confirmar a operação
    tratativa_erro()  # Chamar a função para tratar erros antes de continuar
    show_info("Sucesso", "Usuário cadastrado com sucesso.")

    if g.AUTEN_FORM is not None:
        g.AUTEN_FORM.close()

    if callable(habilitar_janelas):
        habilitar_janelas()


def login():
    """
    Realiza o login do usuário com o nome e senha fornecidos.
    Se o usuário não existir, cria um novo usuário.
    """
    # Verificar se os widgets foram inicializados
    if g.USUARIO_ENTRY is None or g.SENHA_ENTRY is None:
        show_error("Erro", "Interface não inicializada corretamente.")
        return

    g.USUARIO_NOME = g.USUARIO_ENTRY.text() if g.USUARIO_ENTRY else ""
    usuario_senha = g.SENHA_ENTRY.text() if g.SENHA_ENTRY else ""

    usuario_obj = session.query(Usuario).filter_by(nome=g.USUARIO_NOME).first()

    if usuario_obj:
        # Usar getattr para acessar o valor da coluna de forma segura
        senha_db = getattr(usuario_obj, "senha", None)
        if senha_db == "nova_senha":
            nova_senha = ask_string(
                "Nova Senha",
                "Digite uma nova senha:",
                parent=g.AUTEN_FORM if g.AUTEN_FORM else None,
            )
            if nova_senha:
                # Usar setattr para atribuir valor à coluna de forma segura
                senha_hash = hashlib.sha256(nova_senha.encode()).hexdigest()
                setattr(usuario_obj, "senha", senha_hash)
                tratativa_erro()
                show_info(
                    "Sucesso",
                    "Senha alterada com sucesso. Faça login novamente.",
                    parent=g.AUTEN_FORM if g.AUTEN_FORM else None,
                )
                return
        elif senha_db == hashlib.sha256(usuario_senha.encode()).hexdigest():
            show_info(
                "Login",
                "Login efetuado com sucesso.",
                parent=g.AUTEN_FORM if g.AUTEN_FORM else None,
            )
            g.USUARIO_ID = usuario_obj.id
            if g.AUTEN_FORM is not None:
                g.AUTEN_FORM.close()
            if g.PRINC_FORM is not None:
                titulo = f"Cálculo de Dobra - {getattr(usuario_obj, 'nome', 'Usuário')}"
                g.PRINC_FORM.setWindowTitle(titulo)
            # Atualiza a barra de título customizada, se existir
            if hasattr(g, "BARRA_TITULO") and g.BARRA_TITULO:
                g.BARRA_TITULO.titulo.setText(titulo)
        else:
            show_error(
                "Erro",
                "Usuário ou senha incorretos.",
                parent=g.AUTEN_FORM if g.AUTEN_FORM else None,
            )
    else:
        show_error(
            "Erro",
            "Usuário ou senha incorretos.",
            parent=g.AUTEN_FORM if g.AUTEN_FORM else None,
        )

    if callable(habilitar_janelas):
        habilitar_janelas()


def logado(tipo):
    """
    Verifica se o usuário está logado antes de permitir ações em formulários específicos.
    """
    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]

    if g.USUARIO_ID is None:
        show_error("Erro", "Login requerido.", parent=config["form"])
        return False
    return True


def tem_permissao(tipo, role_requerida, show_message=True):
    """
    Verifica se o usuário tem permissão para realizar uma ação específica.

    Args:
        tipo (str): O tipo de configuração a ser usado.
        role_requerida (str): O nível de permissão necessário ('viewer', 'editor', 'admin').
        show_message (bool): Se False, suprime a exibição de mensagens de erro.
    """
    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]

    usuario_obj = session.query(Usuario).filter_by(id=g.USUARIO_ID).first()
    if not usuario_obj:
        if show_message:
            show_error(
                "Erro",
                "Você não tem permissão para acessar esta função.",
                parent=config["form"],
            )
        return False

    # Permitir hierarquia de permissões
    roles_hierarquia = ["viewer", "editor", "admin"]
    usuario_role = getattr(usuario_obj, "role", "viewer")

    try:
        required_index = roles_hierarquia.index(role_requerida)
        user_index = roles_hierarquia.index(usuario_role)
    except ValueError:
        if show_message:
            show_error("Erro", "Role de usuário inválida encontrada.")
        return False

    if user_index < required_index:
        if show_message:
            show_error("Erro", f"Permissão '{role_requerida}' requerida.")
        return False
    return True


def logout():
    """
    Realiza o logout do usuário atual.
    """
    if g.USUARIO_ID is None:
        show_error("Erro", "Nenhum usuário logado.")
        return

    g.USUARIO_ID = None
    if g.PRINC_FORM is not None:
        g.PRINC_FORM.setWindowTitle("Cálculo de Dobra")
        if hasattr(g, "BARRA_TITULO") and g.BARRA_TITULO:
            g.BARRA_TITULO.titulo.setText("Cálculo de Dobra")
    show_info("Logout", "Logout efetuado com sucesso.")


def resetar_senha():
    """
    Reseta a senha do usuário selecionado na lista de usuários.
    """
    if g.LIST_USUARIO is None:
        show_error("Erro", "Lista de usuários não inicializada.")
        return

    # Usar item_selecionado_usuario para obter o item de forma compatível com PySide6
    user_id = item_selecionado_usuario()
    if user_id is None:
        show_warning(
            "Aviso",
            "Selecione um usuário para resetar a senha.",
            parent=g.USUAR_FORM if g.USUAR_FORM else None,
        )
        return

    novo_password = "nova_senha"  # Defina a nova senha padrão aqui
    usuario_obj = session.query(Usuario).filter_by(id=user_id).first()
    if usuario_obj:
        setattr(usuario_obj, "senha", novo_password)
        tratativa_erro()
        show_info(
            "Sucesso",
            "Senha resetada com sucesso.",
            parent=g.USUAR_FORM if g.USUAR_FORM else None,
        )
    else:
        show_error(
            "Erro",
            "Usuário não encontrado.",
            parent=g.USUAR_FORM if g.USUAR_FORM else None,
        )


def excluir_usuario():
    """
    Exclui o usuário selecionado na lista de usuários.
    """
    # Validações iniciais
    if not tem_permissao("usuario", "admin") or g.LIST_USUARIO is None:
        return

    # Usar item_selecionado_usuario para obter o item de forma compatível com PySide6
    obj_id = item_selecionado_usuario()
    if obj_id is None:
        show_warning(
            "Aviso",
            "Selecione um usuário para excluir.",
            parent=g.USUAR_FORM if g.USUAR_FORM else None,
        )
        return

    # Obter dados do usuário selecionado
    obj = session.query(Usuario).filter_by(id=obj_id).first()

    erro_msg = None
    if obj is None:
        erro_msg = "Usuário não encontrado."
    elif getattr(obj, "role", None) == "admin":
        erro_msg = "Não é possível excluir um administrador."

    if erro_msg:
        show_error("Erro", erro_msg, parent=g.USUAR_FORM if g.USUAR_FORM else None)
        return

    # Confirmar exclusão
    aviso = QMessageBox.question(
        g.USUAR_FORM if g.USUAR_FORM else None,
        "Atenção!",
        "Tem certeza que deseja excluir o usuário?",
        QMessageBox.Yes | QMessageBox.No,
    )
    if aviso == QMessageBox.Yes:
        session.delete(obj)
        tratativa_erro()
        # Atualizar a lista após exclusão
        listar("usuario")
        show_info(
            "Sucesso",
            "Usuário excluído com sucesso!",
            parent=g.USUAR_FORM if g.USUAR_FORM else None,
        )


def tornar_editor():
    """
    Promove o usuário selecionado a editor.
    """
    if g.LIST_USUARIO is None:
        show_error("Erro", "Lista de usuários não disponível.")
        return

    # Usar item_selecionado_usuario para obter o item de forma compatível com PySide6
    user_id = item_selecionado_usuario()
    if user_id is None:
        show_warning(
            "Aviso",
            "Selecione um usuário para promover a editor.",
            parent=g.USUAR_FORM if g.USUAR_FORM else None,
        )
        return

    usuario_obj = session.query(Usuario).filter_by(id=user_id).first()

    if usuario_obj:
        # Usar getattr para acessar o valor da coluna de forma segura
        usuario_role = getattr(usuario_obj, "role", None)
        if usuario_role == "admin":
            show_error(
                "Erro",
                "O usuário já é um administrador.",
                parent=g.USUAR_FORM if g.USUAR_FORM else None,
            )
            return
        if usuario_role == "editor":
            show_info(
                "Informação",
                "O usuário já é um editor.",
                parent=g.USUAR_FORM if g.USUAR_FORM else None,
            )
            return

        # Usar setattr para atribuir valor à coluna de forma segura
        setattr(usuario_obj, "role", "editor")
        tratativa_erro()
        show_info(
            "Sucesso",
            "Usuário promovido a editor com sucesso.",
            parent=g.USUAR_FORM if g.USUAR_FORM else None,
        )
        listar("usuario")  # Atualiza a lista de usuários na interface
    else:
        show_error(
            "Erro",
            "Usuário não encontrado.",
            parent=g.USUAR_FORM if g.USUAR_FORM else None,
        )


def item_selecionado_usuario():
    """
    Retorna o ID do usuário selecionado na lista de usuários.
    """
    if g.LIST_USUARIO is None:
        return None

    selected_items = g.LIST_USUARIO.selectedItems()
    if not selected_items:
        return None

    selected_item = selected_items[0]
    try:
        # Para lista de usuários, o ID está na primeira coluna (ID, Nome, Role)
        user_id = selected_item.text(0)
        return int(user_id)
    except (ValueError, IndexError):
        return None
