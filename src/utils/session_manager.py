"""
Gerenciamento de sessões do sistema, incluindo registro,
remoção e verificação de comandos do sistema.
"""

import logging
import socket
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Optional, Type

from sqlalchemy.exc import SQLAlchemyError

from src.models.models import SystemControl as SystemControlModel
from src.utils.banco_dados import Session
from src.utils.banco_dados import session as db_session

SESSION_ID = str(uuid.uuid4())


def registrar_sessao():
    """Registra a sessão atual no banco de dados."""
    try:
        hostname = socket.gethostname()
        sessao_existente = (
            db_session.query(SystemControlModel).filter_by(key=SESSION_ID).first()
        )
        if not sessao_existente:
            logging.info(
                "Registrando nova sessão: ID %s para host %s", SESSION_ID, hostname
            )
            nova_sessao = SystemControlModel(
                type="SESSION", key=SESSION_ID, value=hostname
            )
            db_session.add(nova_sessao)
            db_session.commit()
    except SQLAlchemyError as e:
        logging.error("Erro ao registrar sessão: %s", e)
        db_session.rollback()


def remover_sessao():
    """Remove a sessão atual do banco de dados de forma segura ao fechar."""
    # Usa uma nova sessão para garantir que a operação seja concluída mesmo se a global for fechada
    scoped_session = Session()
    try:
        logging.info("Removendo sessão: ID %s", SESSION_ID)
        sessao_para_remover = (
            scoped_session.query(SystemControlModel).filter_by(key=SESSION_ID).first()
        )
        if sessao_para_remover:
            scoped_session.delete(sessao_para_remover)
            scoped_session.commit()
            logging.info("Sessão %s removida com sucesso.", SESSION_ID)
    except SQLAlchemyError as e:
        logging.error("Erro ao remover sessão: %s", e)
        scoped_session.rollback()
    finally:
        scoped_session.close()


def limpar_sessoes_inativas(timeout_minutos: int = 2):
    """
    Verifica e remove sessões que não foram atualizadas (heartbeat)
    dentro do tempo limite especificado.
    """
    # Usa uma nova sessão para operações em background seguras
    scoped_session = Session()
    try:
        limite_tempo = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutos)
        logging.info(
            "Limpando sessões inativas mais antigas que %s",
            limite_tempo.strftime("%Y-%m-%d %H:%M:%S"),
        )

        sessoes_inativas = (
            scoped_session.query(SystemControlModel)
            .filter(
                SystemControlModel.type == "SESSION",
                SystemControlModel.last_updated < limite_tempo,
            )
            .all()
        )

        if not sessoes_inativas:
            logging.info("Nenhuma sessão inativa encontrada.")
            return

        for sessao in sessoes_inativas:
            logging.warning(
                "Removendo sessão inativa: ID %s, Host: %s, Última atualização: %s",
                sessao.key,
                sessao.value,
                sessao.last_updated,
            )
            scoped_session.delete(sessao)

        scoped_session.commit()
        logging.info("%d sessão(ões) inativa(s) removida(s).", len(sessoes_inativas))

    except SQLAlchemyError as e:
        logging.error("Erro ao limpar sessões inativas: %s", e)
        scoped_session.rollback()
    finally:
        scoped_session.close()


def atualizar_heartbeat_sessao():
    """Atualiza o timestamp da sessão ativa para indicar que está online."""
    try:
        sessao_atual = (
            db_session.query(SystemControlModel).filter_by(key=SESSION_ID).first()
        )
        if sessao_atual:
            sessao_atual.last_updated = datetime.now(timezone.utc)
            db_session.commit()
        else:
            registrar_sessao()
    except SQLAlchemyError as e:
        logging.error("Erro ao atualizar heartbeat da sessão: %s", e)
        db_session.rollback()


def obter_sessoes_ativas():
    """Retorna lista de todas as sessões ativas."""
    try:
        sessoes = (
            db_session.query(SystemControlModel)
            .filter_by(type="SESSION")
            .order_by(SystemControlModel.last_updated.desc())
            .all()
        )
        resultado = []
        for sessao in sessoes:
            resultado.append(
                {
                    "session_id": sessao.key,
                    "hostname": sessao.value,
                    "last_updated": (
                        sessao.last_updated.strftime("%Y-%m-%d %H:%M:%S")
                        if sessao.last_updated
                        else "N/A"
                    ),
                }
            )
        return resultado
    except SQLAlchemyError as e:
        logging.error("Erro ao obter sessões ativas: %s", e)
        db_session.rollback()
        return []


def verificar_comando_sistema() -> bool:
    """
    Verifica se há um comando de sistema para desligar a aplicação.
    Retorna True se o comando 'SHUTDOWN' for encontrado, False caso contrário.
    Esta função não modifica o comando, apenas o lê.
    """
    # Usa uma nova sessão para garantir leitura isolada e segura
    scoped_session = Session()
    try:
        cmd_entry = (
            scoped_session.query(SystemControlModel).filter_by(key="UPDATE_CMD").first()
        )

        if cmd_entry and cmd_entry.value == "SHUTDOWN":
            logging.warning("Comando SHUTDOWN recebido. Sinalizando para encerrar.")
            return True

    except SQLAlchemyError as e:
        logging.error("Erro ao verificar comando do sistema: %s", e)
        scoped_session.rollback()
    finally:
        scoped_session.close()

    return False  # Nenhum comando de shutdown encontrado


def force_shutdown_all_instances(
    session: Any,
    model: Type[SystemControlModel],
    progress_callback: Optional[Callable[[int], None]] = None,
) -> bool:
    """Força o encerramento de todas as instâncias da aplicação."""
    logging.info("A enviar comando de encerramento...")
    try:
        cmd_entry = session.query(model).filter_by(key="UPDATE_CMD").first()
        if cmd_entry:
            cmd_entry.value = "SHUTDOWN"
            cmd_entry.last_updated = datetime.now(timezone.utc)
        else:
            new_cmd = model(key="UPDATE_CMD", value="SHUTDOWN", type="COMMAND")
            session.add(new_cmd)
        session.commit()

        start_time = time.time()
        while (time.time() - start_time) < 60:
            active_sessions = session.query(model).filter_by(type="SESSION").count()
            if progress_callback:
                progress_callback(active_sessions)
            if active_sessions == 0:
                logging.info("Todas as instâncias foram fechadas.")
                if progress_callback:
                    progress_callback(0)
                return True
            time.sleep(2)
        logging.error("Timeout! As instâncias não fecharam a tempo.")
        return False
    finally:
        cmd_entry = session.query(model).filter_by(key="UPDATE_CMD").first()
        if cmd_entry and cmd_entry.value == "SHUTDOWN":
            cmd_entry.value = "NONE"
            session.commit()
