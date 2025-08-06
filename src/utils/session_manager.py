"""
Gerenciamento de sessões do sistema, incluindo registro,
remoção e verificação de comandos do sistema.
"""

import logging
import socket
import uuid
from datetime import datetime, timezone

from sqlalchemy.exc import SQLAlchemyError

from src.models.models import SystemControl
from src.utils.banco_dados import session as db_session

SESSION_ID = str(uuid.uuid4())


def registrar_sessao():
    """Registra a sessão atual no banco de dados."""
    try:
        hostname = socket.gethostname()
        sessao_existente = (
            db_session.query(SystemControl).filter_by(key=SESSION_ID).first()
        )
        if not sessao_existente:
            logging.info(
                "Registrando nova sessão: ID %s para host %s", SESSION_ID, hostname
            )
            nova_sessao = SystemControl(
                type="SESSION", key=SESSION_ID, value=hostname
            )
            db_session.add(nova_sessao)
            db_session.commit()
    except SQLAlchemyError as e:
        logging.error("Erro ao registrar sessão: %s", e)
        db_session.rollback()


def remover_sessao():
    """Remove a sessão atual do banco de dados ao fechar."""
    try:
        logging.info("Removendo sessão: ID %s", SESSION_ID)
        sessao_para_remover = (
            db_session.query(SystemControl).filter_by(key=SESSION_ID).first()
        )
        if sessao_para_remover:
            db_session.delete(sessao_para_remover)
            db_session.commit()
    except SQLAlchemyError as e:
        logging.error("Erro ao remover sessão: %s", e)
        db_session.rollback()


def atualizar_heartbeat_sessao():
    """Atualiza o timestamp da sessão ativa para indicar que está online."""
    try:
        sessao_atual = (
            db_session.query(SystemControl).filter_by(key=SESSION_ID).first()
        )
        if sessao_atual:
            sessao_atual.last_updated = datetime.now(timezone.utc)
            db_session.commit()
        else:
            # Se a sessão não existe por algum motivo, registra novamente.
            registrar_sessao()
    except SQLAlchemyError as e:
        logging.error("Erro ao atualizar heartbeat da sessão: %s", e)
        db_session.rollback()


def obter_comando_sistema() -> str | None:
    """Busca no banco e retorna o comando atual do sistema ('SHUTDOWN', 'NONE', etc.)."""
    try:
        cmd_entry = db_session.query(SystemControl).filter_by(key="UPDATE_CMD").first()
        return str(cmd_entry.value) if cmd_entry and cmd_entry.value else None
    except SQLAlchemyError as e:
        logging.error("Erro ao obter comando do sistema: %s", e)
        db_session.rollback()
        return None
