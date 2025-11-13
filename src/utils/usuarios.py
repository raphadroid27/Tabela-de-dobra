"""Módulo utilitário para gerenciamento de usuários (Refatorado).

Atualizado para usar o padrão de sessão por operação.
"""

import hashlib
import logging

from sqlalchemy.exc import SQLAlchemyError

from src.config import globals as g
from src.models.models import Usuario
from src.utils.banco_dados import get_session
from src.utils.interface import obter_configuracoes
from src.utils.janelas import Janela
from src.utils.utilitarios import (
    ask_string,
    ask_yes_no,
    show_error,
    show_info,
    show_warning,
)

RESET_PASSWORD_SENTINEL = ""
RESET_PASSWORD_HASH = hashlib.sha256(RESET_PASSWORD_SENTINEL.encode()).hexdigest()


def _obter_usuario_logado(session):
    """Obtém o usuário logado com verificação de segurança.

    Returns:
        Usuario ou None: O objeto usuario se logado e válido, None caso contrário.
    """
    if g.USUARIO_ID is None:
        return None
    return session.get(Usuario, g.USUARIO_ID)


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

    try:
        with get_session() as session:
            if session.query(Usuario).filter_by(nome=novo_usuario_nome).first():
                show_error("Erro", "Usuário já existente.")
                return

            senha_hash = hashlib.sha256(novo_usuario_senha.encode()).hexdigest()
            role = g.ADMIN_VAR or "viewer"
            usuario = Usuario(nome=novo_usuario_nome, senha=senha_hash, role=role)
            session.add(usuario)

        show_info("Sucesso", "Usuário cadastrado com sucesso.")
        if g.AUTEN_FORM:
            g.AUTEN_FORM.close()
        Janela.estado_janelas(True)

    except SQLAlchemyError as e:
        logging.error("Erro de DB ao criar usuário: %s", e)
        show_error("Erro", "Não foi possível criar o usuário.")


# pylint: disable=R0912


def login():
    """Realiza o login do usuário com o nome e senha fornecidos."""
    if g.USUARIO_ENTRY is None or g.SENHA_ENTRY is None:
        show_error("Erro", "Interface não inicializada corretamente.")
        return

    g.USUARIO_NOME = g.USUARIO_ENTRY.text()
    usuario_senha = g.SENHA_ENTRY.text()
    parent_form = g.AUTEN_FORM

    try:
        with get_session() as session:
            usuario_obj = session.query(Usuario).filter_by(nome=g.USUARIO_NOME).first()

            if not usuario_obj:
                show_error("Erro", "Usuário ou senha incorretos.", parent=parent_form)
                return

            senha_hash_informada = hashlib.sha256(usuario_senha.encode()).hexdigest()

            if usuario_obj.senha == RESET_PASSWORD_HASH:
                nova_senha = ask_string(
                    "Nova Senha", "Digite uma nova senha:", parent=parent_form
                )
                if nova_senha:
                    nova_senha = nova_senha.strip()
                    if nova_senha:
                        usuario_obj.senha = hashlib.sha256(
                            nova_senha.encode()
                        ).hexdigest()
                        show_info(
                            "Sucesso",
                            "Senha alterada. Faça login novamente.",
                            parent=parent_form,
                        )
                    else:
                        show_warning(
                            "Aviso",
                            "Senha não pode ser vazia. "
                            "Repita o processo de login para definir uma nova senha.",
                            parent=parent_form,
                        )
                else:
                    show_warning(
                        "Aviso",
                        "Senha não alterada. "
                        "Repita o processo de login para definir uma nova senha.",
                        parent=parent_form,
                    )
                return

            if usuario_obj.senha == senha_hash_informada:
                show_info("Login", "Login efetuado com sucesso.", parent=parent_form)
                g.USUARIO_ID = usuario_obj.id
                if parent_form:
                    parent_form.close()
                if g.PRINC_FORM:
                    titulo = f"Calculadora de Dobra - {usuario_obj.nome}"
                    g.PRINC_FORM.setWindowTitle(titulo)
                return

            show_error("Erro", "Usuário ou senha incorretos.", parent=parent_form)

    except SQLAlchemyError as e:
        logging.error("Erro de DB no login: %s", e)
        show_error("Erro", "Não foi possível realizar o login.", parent=parent_form)
    finally:
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
    try:
        with get_session() as session:
            usuario_obj = _obter_usuario_logado(session)
            if not usuario_obj:
                if show_message:
                    show_warning(
                        "Aviso", "Você não tem permissão.", parent=config["form"]
                    )
                return False

            roles_hierarquia = ["viewer", "editor", "admin"]
            required_index = roles_hierarquia.index(role_requerida)
            user_index = roles_hierarquia.index(usuario_obj.role)

            if user_index < required_index:
                if show_message:
                    show_error("Erro", f"Permissão '{role_requerida}' requerida.")
                return False
            return True
    except (SQLAlchemyError, ValueError) as e:
        if show_message:
            show_error("Erro", f"Erro ao verificar permissão: {e}")
        return False


def logout():
    """Realiza o logout do usuário atual."""
    if g.USUARIO_ID is None:
        show_error("Erro", "Nenhum usuário logado.")
        return

    g.USUARIO_ID = None
    if g.PRINC_FORM:
        titulo = "Calculadora de Dobra"
        g.PRINC_FORM.setWindowTitle(titulo)
    show_info("Logout", "Logout efetuado com sucesso.")


def item_selecionado_usuario():
    """Retorna o ID do usuário selecionado na lista de usuários."""
    if g.LIST_USUARIO is None:
        return None
    current_row = g.LIST_USUARIO.currentRow()
    if current_row < 0:
        return None
    id_item = g.LIST_USUARIO.item(current_row, 0)
    if id_item is None:
        return None
    try:
        return int(id_item.text())
    except (ValueError, TypeError):
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
        with get_session() as session:
            usuario_obj = session.get(Usuario, user_id)
            if usuario_obj:
                usuario_obj.senha = RESET_PASSWORD_HASH
                show_info(
                    "Sucesso",
                    "Senha resetada. Ao fazer login, "
                    "será solicitado que o usuário defina uma nova senha.",
                    parent=parent,
                )
                return True
            show_error("Erro", "Usuário não encontrado.", parent=parent)
            return False
    except SQLAlchemyError as e:
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
        with get_session() as session:
            usuario_obj = session.get(Usuario, user_id)
            if usuario_obj:
                session.delete(usuario_obj)
                show_info("Sucesso", "Usuário excluído com sucesso!", parent=parent)
                return True
            show_error("Erro", "Usuário não encontrado para exclusão.", parent=parent)
            return False
    except SQLAlchemyError as e:
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
        with get_session() as session:
            usuario_obj = session.get(Usuario, user_id)
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
            show_info("Sucesso", mensagem, parent=parent)
            return True
    except SQLAlchemyError as e:
        logging.error("Erro de DB ao alterar permissão: %s", e)
        show_error("Erro", f"Erro de banco de dados: {e}", parent=parent)
        return False
