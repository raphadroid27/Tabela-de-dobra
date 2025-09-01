"""
Módulo utilitário para gerenciamento de usuários no aplicativo de cálculo de dobras.
Contém a lógica centralizada para criação, autenticação e manipulação de usuários.
"""

import hashlib
import logging

from sqlalchemy.exc import SQLAlchemyError

from src.config import globals as g
from src.models.models import Usuario
from src.utils.banco_dados import Session, tratativa_erro
from src.utils.interface import obter_configuracoes
from src.utils.janelas import Janela
from src.utils.utilitarios import (
    ask_string,
    ask_yes_no,
    show_error,
    show_info,
    show_warning,
)


def novo_usuario():
    """Cria um novo usuário com o nome e senha fornecidos."""
    if g.USUARIO_ENTRY is None or g.SENHA_ENTRY is None:
        show_error("Erro", "Interface não inicializada corretamente.")
        return

    novo_usuario_nome = g.USUARIO_ENTRY.text()
    novo_usuario_senha = g.SENHA_ENTRY.text()

    if not novo_usuario_nome or not novo_usuario_senha:
        show_error("Erro", "Preencha todos os campos.")
        return

    if Session.query(Usuario).filter_by(nome=novo_usuario_nome).first():
        show_error("Erro", "Usuário já existente.")
        return

    senha_hash = hashlib.sha256(novo_usuario_senha.encode()).hexdigest()
    role = g.ADMIN_VAR or "viewer"
    usuario = Usuario(nome=novo_usuario_nome, senha=senha_hash, role=role)
    Session.add(usuario)

    tratativa_erro()
    show_info("Sucesso", "Usuário cadastrado com sucesso.")

    if g.AUTEN_FORM:
        g.AUTEN_FORM.close()

    Janela.estado_janelas(True)


def login():
    """Realiza o login do usuário com o nome e senha fornecidos."""
    if g.USUARIO_ENTRY is None or g.SENHA_ENTRY is None:
        show_error("Erro", "Interface não inicializada corretamente.")
        return

    g.USUARIO_NOME = g.USUARIO_ENTRY.text()
    usuario_senha = g.SENHA_ENTRY.text()
    parent_form = g.AUTEN_FORM

    usuario_obj = Session.query(Usuario).filter_by(nome=g.USUARIO_NOME).first()

    if not usuario_obj:
        show_error("Erro", "Usuário ou senha incorretos.", parent=parent_form)
        return

    if usuario_obj.senha == "nova_senha":
        nova_senha = ask_string(
            "Nova Senha", "Digite uma nova senha:", parent=parent_form
        )
        if nova_senha:
            usuario_obj.senha = hashlib.sha256(nova_senha.encode()).hexdigest()
            tratativa_erro()
            show_info(
                "Sucesso", "Senha alterada. Faça login novamente.", parent=parent_form
            )
    elif usuario_obj.senha == hashlib.sha256(usuario_senha.encode()).hexdigest():
        show_info("Login", "Login efetuado com sucesso.", parent=parent_form)
        g.USUARIO_ID = usuario_obj.id
        if parent_form:
            parent_form.close()
        if g.PRINC_FORM:
            titulo = f"Calculadora de Dobra - {usuario_obj.nome}"
            g.PRINC_FORM.setWindowTitle(titulo)
            if hasattr(g, "BARRA_TITULO") and g.BARRA_TITULO:
                g.BARRA_TITULO.titulo.setText(titulo)
    else:
        show_error("Erro", "Usuário ou senha incorretos.", parent=parent_form)

    Janela.estado_janelas(True)


def logado(tipo):
    """Verifica se o usuário está logado antes de permitir ações."""
    config = obter_configuracoes()[tipo]
    if g.USUARIO_ID is None:
        show_error("Erro", "Login requerido.", parent=config["form"])
        return False
    return True


def tem_permissao(tipo, role_requerida, show_message=True):
    """Verifica se o usuário tem a permissão necessária."""
    config = obter_configuracoes()[tipo]
    usuario_obj = Session.query(Usuario).filter_by(id=g.USUARIO_ID).first()

    if not usuario_obj:
        if show_message:
            show_warning("Aviso", "Você não tem permissão.", parent=config["form"])
        return False

    roles_hierarquia = ["viewer", "editor", "admin"]
    try:
        required_index = roles_hierarquia.index(role_requerida)
        user_index = roles_hierarquia.index(usuario_obj.role)
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
    """Realiza o logout do usuário atual."""
    if g.USUARIO_ID is None:
        show_error("Erro", "Nenhum usuário logado.")
        return

    g.USUARIO_ID = None
    if g.PRINC_FORM:
        titulo = "Calculadora de Dobra"
        g.PRINC_FORM.setWindowTitle(titulo)
        if hasattr(g, "BARRA_TITULO") and g.BARRA_TITULO:
            g.BARRA_TITULO.titulo.setText(titulo)
    show_info("Logout", "Logout efetuado com sucesso.")


def item_selecionado_usuario():
    """Retorna o ID do usuário selecionado na lista de usuários."""
    if g.LIST_USUARIO is None:
        return None
    selected_items = g.LIST_USUARIO.selectedItems()
    if not selected_items:
        return None
    try:
        return int(selected_items[0].text(0))
    except (ValueError, IndexError):
        return None


def resetar_senha(parent=None):
    """Reseta a senha do usuário selecionado."""
    user_id = item_selecionado_usuario()
    if user_id is None:
        show_warning(
            "Aviso", "Selecione um usuário para resetar a senha.", parent=parent
        )
        return False

    try:
        usuario_obj = Session.query(Usuario).filter_by(id=user_id).first()
        if usuario_obj:
            usuario_obj.senha = "nova_senha"
            tratativa_erro()
            show_info("Sucesso", "Senha resetada com sucesso.", parent=parent)
            return True

        show_error("Erro", "Usuário não encontrado.", parent=parent)
        return False
    except SQLAlchemyError as e:
        Session.rollback()
        logging.error("Erro de DB ao resetar senha: %s", e)
        show_error("Erro", f"Erro de banco de dados: {e}", parent=parent)
        return False


def excluir_usuario(parent=None):
    """Exclui o usuário selecionado."""
    if not tem_permissao("usuario", "admin", show_message=False):
        show_error("Erro", "Permissão 'admin' requerida.", parent=parent)
        return False

    user_id = item_selecionado_usuario()
    if user_id is None:
        show_warning("Aviso", "Selecione um usuário para excluir.", parent=parent)
        return False

    if not ask_yes_no(
        "Atenção!", "Tem certeza que deseja excluir o usuário?", parent=parent
    ):
        return False

    try:
        usuario_obj = Session.query(Usuario).filter_by(id=user_id).first()
        if usuario_obj:
            Session.delete(usuario_obj)
            tratativa_erro()
            show_info("Sucesso", "Usuário excluído com sucesso!", parent=parent)
            return True

        show_error("Erro", "Usuário não encontrado para exclusão.", parent=parent)
        return False
    except SQLAlchemyError as e:
        Session.rollback()
        logging.error("Erro de DB ao excluir usuário: %s", e)
        show_error(
            "Erro", f"Erro de banco de dados ao excluir usuário: {e}", parent=parent
        )
        return False


def alternar_permissao_editor(parent=None):
    """Alterna a permissão do usuário selecionado entre 'editor' e 'viewer'."""
    if not tem_permissao("usuario", "admin", show_message=False):
        show_error("Erro", "Permissão 'admin' requerida.", parent=parent)
        return False

    user_id = item_selecionado_usuario()
    if user_id is None:
        show_warning(
            "Aviso", "Selecione um usuário para alterar a permissão.", parent=parent
        )
        return False

    try:
        usuario_obj = Session.query(Usuario).filter_by(id=user_id).first()
        if not usuario_obj:
            show_error("Erro", "Usuário não encontrado.", parent=parent)
            return False

        if usuario_obj.role == "admin":
            show_error(
                "Erro",
                "Não é possível alterar a permissão de um administrador.",
                parent=parent,
            )
            return False

        if usuario_obj.role == "editor":
            nova_permissao = "viewer"
            mensagem = (
                f"Permissão do usuário '{usuario_obj.nome}' alterada para 'viewer'."
            )
        else:
            nova_permissao = "editor"
            mensagem = f"Usuário '{usuario_obj.nome}' promovido a 'editor'."

        usuario_obj.role = nova_permissao
        tratativa_erro()
        show_info("Sucesso", mensagem, parent=parent)
        return True
    except SQLAlchemyError as e:
        Session.rollback()
        logging.error("Erro de DB ao alterar permissão: %s", e)
        show_error("Erro", f"Erro de banco de dados: {e}", parent=parent)
        return False
