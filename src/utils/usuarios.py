"""
Módulo utilitário para gerenciamento de usuários.
Versão corrigida para usar o context manager 'session_scope' para
todas as operações de banco de dados, garantindo segurança em ambiente multi-thread.
"""

import hashlib

from sqlalchemy.exc import SQLAlchemyError

from src.config import globals as g
from src.models.models import Usuario

# ADICIONADO: session_scope
from src.utils.banco_dados import session_scope
from src.utils.interface import listar, obter_configuracoes
from src.utils.janelas import Janela

# MODIFICADO: Importação completa das funções de mensagem
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

    novo_usuario_nome = g.USUARIO_ENTRY.text() or ""
    novo_usuario_senha = g.SENHA_ENTRY.text() or ""

    if not novo_usuario_nome or not novo_usuario_senha:
        show_error("Erro", "Preencha todos os campos.")
        return

    senha_hash = hashlib.sha256(novo_usuario_senha.encode()).hexdigest()
    admin_value = g.ADMIN_VAR or "viewer"

    try:
        with session_scope() as db_session:
            usuario_existente = (
                db_session.query(Usuario).filter_by(nome=novo_usuario_nome).first()
            )
            if usuario_existente:
                show_error("Erro", "Usuário já existente.")
                return

            usuario = Usuario(
                nome=novo_usuario_nome, senha=senha_hash, role=admin_value
            )
            db_session.add(usuario)
            # O commit é feito automaticamente ao sair do 'with'

        show_info("Sucesso", "Usuário cadastrado com sucesso.")
        if g.AUTEN_FORM:
            g.AUTEN_FORM.close()
        Janela.estado_janelas(True)

    except SQLAlchemyError as e:
        show_error("Erro", f"Erro de banco de dados ao criar usuário: {e}")


def login():
    """Realiza o login do usuário com o nome e senha fornecidos."""
    if g.USUARIO_ENTRY is None or g.SENHA_ENTRY is None:
        show_error("Erro", "Interface não inicializada corretamente.")
        return

    g.USUARIO_NOME = g.USUARIO_ENTRY.text() or ""
    usuario_senha = g.SENHA_ENTRY.text() or ""
    senha_hash_digitada = hashlib.sha256(usuario_senha.encode()).hexdigest()

    try:
        with session_scope() as db_session:
            usuario_obj = (
                db_session.query(Usuario).filter_by(nome=g.USUARIO_NOME).first()
            )

            if not usuario_obj:
                show_error("Erro", "Usuário ou senha incorretos.")
                return

            # Expunge o objeto para que possa ser usado fora da sessão
            db_session.expunge(usuario_obj)

        # Lógica de verificação de senha fora da sessão do DB
        senha_db = getattr(usuario_obj, "senha", None)

        if senha_db == "nova_senha":
            # Esta parte precisa de uma nova sessão para atualizar a senha
            _atualizar_nova_senha(usuario_obj)
            return

        if senha_db == senha_hash_digitada:
            show_info("Login", "Login efetuado com sucesso.")
            g.USUARIO_ID = usuario_obj.id
            if g.AUTEN_FORM:
                g.AUTEN_FORM.close()
            if g.PRINC_FORM:
                titulo = f"Calculadora de Dobra - {getattr(usuario_obj, 'nome', 'Usuário')}"
                g.PRINC_FORM.setWindowTitle(titulo)
            if hasattr(g, "BARRA_TITULO") and g.BARRA_TITULO:
                g.BARRA_TITULO.titulo.setText(titulo)
        else:
            show_error("Erro", "Usuário ou senha incorretos.")

    except SQLAlchemyError as e:
        show_error("Erro", f"Erro de banco de dados durante o login: {e}")
    finally:
        Janela.estado_janelas(True)


def _atualizar_nova_senha(usuario_obj):
    """Função auxiliar para solicitar e atualizar uma nova senha."""
    nova_senha = ask_string("Nova Senha", "Digite uma nova senha:", parent=g.AUTEN_FORM)
    if not nova_senha:
        return

    nova_senha_hash = hashlib.sha256(nova_senha.encode()).hexdigest()
    try:
        with session_scope() as db_session:
            db_session.query(Usuario).filter_by(id=usuario_obj.id).update(
                {"senha": nova_senha_hash}
            )
        show_info("Sucesso", "Senha alterada com sucesso. Faça login novamente.")
    except SQLAlchemyError as e:
        show_error("Erro", f"Não foi possível atualizar a senha: {e}")


def logado(tipo):
    """Verifica se o usuário está logado."""
    if g.USUARIO_ID is None:
        config = obter_configuracoes()[tipo]
        show_error("Erro", "Login requerido.", parent=config.get("form"))
        return False
    return True


def tem_permissao(tipo, role_requerida, show_message=True):
    """Verifica se o usuário tem a permissão necessária."""
    if not logado(tipo):
        return False

    try:
        with session_scope() as db_session:
            usuario_obj = db_session.query(Usuario).filter_by(id=g.USUARIO_ID).first()
            if not usuario_obj:
                if show_message:
                    show_warning("Aviso", "Usuário não encontrado ou inválido.")
                return False

            roles_hierarquia = ["viewer", "editor", "admin"]
            usuario_role = getattr(usuario_obj, "role", "viewer")
            required_index = roles_hierarquia.index(role_requerida)
            user_index = roles_hierarquia.index(usuario_role)

            if user_index < required_index:
                if show_message:
                    show_error(
                        "Erro",
                        f"Permissão de '{role_requerida}' ou superior requerida.",
                    )
                return False
            return True
    except (SQLAlchemyError, ValueError) as e:
        if show_message:
            show_error("Erro", f"Erro ao verificar permissões: {e}")
        return False


def logout():
    """Realiza o logout do usuário atual."""
    if g.USUARIO_ID is None:
        show_error("Erro", "Nenhum usuário logado.")
        return

    g.USUARIO_ID = None
    if g.PRINC_FORM:
        g.PRINC_FORM.setWindowTitle("Calculadora de Dobra")
        if hasattr(g, "BARRA_TITULO") and g.BARRA_TITULO:
            g.BARRA_TITULO.titulo.setText("Calculadora de Dobra")
    show_info("Logout", "Logout efetuado com sucesso.")


def resetar_senha():
    """Reseta a senha do usuário selecionado para 'nova_senha'."""
    user_id = item_selecionado_usuario()
    if user_id is None:
        show_warning("Aviso", "Selecione um usuário para resetar a senha.")
        return

    try:
        with session_scope() as db_session:
            updated_count = (
                db_session.query(Usuario)
                .filter_by(id=user_id)
                .update({"senha": "nova_senha"})
            )
            if updated_count > 0:
                show_info(
                    "Sucesso",
                    "Senha resetada. O usuário deverá criar uma nova senha no próximo login.",
                )
            else:
                show_error("Erro", "Usuário não encontrado.")
    except SQLAlchemyError as e:
        show_error("Erro", f"Erro de banco de dados ao resetar senha: {e}")


def excluir_usuario():
    """Exclui o usuário selecionado na lista."""
    if not tem_permissao("usuario", "admin"):
        return

    user_id = item_selecionado_usuario()
    if user_id is None:
        show_warning("Aviso", "Selecione um usuário para excluir.")
        return

    try:
        with session_scope() as db_session:
            usuario_obj = db_session.query(Usuario).filter_by(id=user_id).first()
            if not usuario_obj:
                show_error("Erro", "Usuário não encontrado.")
                return
            if getattr(usuario_obj, "role", None) == "admin":
                show_error("Erro", "Não é possível excluir um administrador.")
                return

            # MODIFICADO: Uso da função ask_yes_no centralizada
            if ask_yes_no(
                "Atenção!",
                "Tem certeza que deseja excluir o usuário?",
                parent=g.USUAR_FORM,
            ):
                db_session.delete(usuario_obj)
                show_info("Sucesso", "Usuário excluído com sucesso!")
                listar("usuario")
    except SQLAlchemyError as e:
        show_error("Erro", f"Erro de banco de dados ao excluir usuário: {e}")


def tornar_editor():
    """Promove o usuário selecionado a editor."""
    if not tem_permissao("usuario", "admin"):
        return

    user_id = item_selecionado_usuario()
    if user_id is None:
        show_warning("Aviso", "Selecione um usuário para promover.")
        return

    try:
        with session_scope() as db_session:
            usuario_obj = db_session.query(Usuario).filter_by(id=user_id).first()
            if not usuario_obj:
                show_error("Erro", "Usuário não encontrado.")
                return
            if usuario_obj.role == "admin":
                show_error("Erro", "O usuário já é um administrador (nível superior).")
                return
            if usuario_obj.role == "editor":
                show_info("Informação", "O usuário já é um editor.")
                return

            usuario_obj.role = "editor"
            show_info("Sucesso", "Usuário promovido a editor com sucesso.")
            listar("usuario")
    except SQLAlchemyError as e:
        show_error("Erro", f"Erro de banco de dados ao promover usuário: {e}")


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
