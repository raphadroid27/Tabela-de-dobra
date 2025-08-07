"""
Gerenciamento de sessões do sistema otimizado para múltiplos usuários,
incluindo registro, remoção e verificação de comandos do sistema.
"""

import logging
import socket
import time
import uuid
from datetime import datetime, timezone
from threading import Timer

from sqlalchemy.exc import SQLAlchemyError

from src.models.models import SystemControl
from src.utils.banco_dados import session as db_session


class SessionManager:
    """Gerenciador de sessões otimizado para múltiplos usuários."""

    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.heartbeat_interval = 60  # 60 segundos
        self.last_heartbeat = 0
        self.heartbeat_timer = None

    def registrar_sessao(self):
        """Registra a sessão atual no banco de dados."""
        try:
            hostname = socket.gethostname()
            sessao_existente = (
                db_session.query(SystemControl).filter_by(key=self.session_id).first()
            )
            if not sessao_existente:
                logging.info(
                    "Registrando nova sessão: ID %s para host %s", self.session_id, hostname
                )
                nova_sessao = SystemControl(
                    type="SESSION", key=self.session_id, value=hostname
                )
                db_session.add(nova_sessao)
                db_session.commit()
        except SQLAlchemyError as e:
            logging.error("Erro ao registrar sessão: %s", e)
            db_session.rollback()

    def remover_sessao(self):
        """Remove a sessão atual do banco de dados ao fechar."""
        try:
            logging.info("Removendo sessão: ID %s", self.session_id)
            sessao_para_remover = (
                db_session.query(SystemControl).filter_by(key=self.session_id).first()
            )
            if sessao_para_remover:
                db_session.delete(sessao_para_remover)
                db_session.commit()
        except SQLAlchemyError as e:
            logging.error("Erro ao remover sessão: %s", e)
            db_session.rollback()
        finally:
            # Cancelar timer se existir
            if self.heartbeat_timer:
                self.heartbeat_timer.cancel()

    def atualizar_heartbeat_sessao(self):
        """Atualiza o timestamp da sessão ativa de forma otimizada para múltiplos usuários."""
        current_time = time.time()

        # Só atualizar se passou o intervalo mínimo (evita spam de updates)
        if current_time - self.last_heartbeat < self.heartbeat_interval:
            return

        try:
            sessao_atual = (
                db_session.query(SystemControl).filter_by(key=self.session_id).first()
            )
            if sessao_atual:
                sessao_atual.last_updated = datetime.now(timezone.utc)
                db_session.commit()
                self.last_heartbeat = current_time
                logging.debug("Heartbeat atualizado para sessão %s", self.session_id)
            else:
                # Se a sessão não existe por algum motivo, registra novamente.
                logging.warning("Sessão não encontrada, reregistrando...")
                self.registrar_sessao()
                self.last_heartbeat = current_time

        except SQLAlchemyError as e:
            logging.error("Erro ao atualizar heartbeat da sessão: %s", e)
            db_session.rollback()

        # Agendar próximo heartbeat automaticamente
        if self.heartbeat_timer:
            self.heartbeat_timer.cancel()

        self.heartbeat_timer = Timer(
            self.heartbeat_interval, self.atualizar_heartbeat_sessao)
        self.heartbeat_timer.daemon = True
        self.heartbeat_timer.start()

    def iniciar_heartbeat_automatico(self):
        """Inicia o sistema de heartbeat automático."""
        self.atualizar_heartbeat_sessao()

    def parar_heartbeat(self):
        """Para o sistema de heartbeat."""
        if self.heartbeat_timer:
            self.heartbeat_timer.cancel()
            self.heartbeat_timer = None

    @staticmethod
    def obter_comando_sistema() -> str | None:
        """Busca no banco e retorna o comando atual do sistema ('SHUTDOWN', 'NONE', etc.)."""
        try:
            cmd_entry = db_session.query(
                SystemControl).filter_by(key="UPDATE_CMD").first()
            return str(cmd_entry.value) if cmd_entry and cmd_entry.value else None
        except SQLAlchemyError as e:
            logging.error("Erro ao obter comando do sistema: %s", e)
            db_session.rollback()
            return None


# Instância global do gerenciador de sessões
session_manager = SessionManager()

# Funções de compatibilidade para manter API existente


def registrar_sessao():
    """Registra a sessão atual no banco de dados."""
    return session_manager.registrar_sessao()


def remover_sessao():
    """Remove a sessão atual do banco de dados ao fechar."""
    return session_manager.remover_sessao()


def atualizar_heartbeat_sessao():
    """Atualiza o heartbeat da sessão."""
    return session_manager.atualizar_heartbeat_sessao()


def obter_comando_sistema() -> str | None:
    """Busca no banco e retorna o comando atual do sistema."""
    return session_manager.obter_comando_sistema()


# Variáveis de compatibilidade
SESSION_ID = session_manager.session_id
