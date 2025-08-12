"""
Gerenciamento de sessões do sistema otimizado para múltiplos usuários,
incluindo registro, remoção e verificação de comandos do sistema.
"""

import logging
import socket
import time
import uuid
from datetime import datetime, timezone
from threading import Lock, Timer
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError

from src.models.models import SystemControl
from src.utils.banco_dados import session_scope  # Importação correta


class SessionManager:
    """Gerenciador de sessões otimizado para múltiplos usuários."""

    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.heartbeat_interval = 60  # 60 segundos
        self.last_heartbeat = 0
        self.heartbeat_timer = None
        self._lock = Lock()

    def registrar_sessao(self):
        """Registra a sessão atual no banco de dados."""
        try:
            with session_scope() as db_session:
                hostname = socket.gethostname()
                sessao_existente = (
                    db_session.query(SystemControl)
                    .filter_by(key=self.session_id)
                    .first()
                )
                if not sessao_existente:
                    logging.info(
                        "Registrando nova sessão: ID %s para host %s",
                        self.session_id,
                        hostname,
                    )
                    nova_sessao = SystemControl(
                        type="SESSION", key=self.session_id, value=hostname
                    )
                    db_session.add(nova_sessao)
        except SQLAlchemyError as e:
            logging.error("Erro ao registrar sessão: %s", e)

    def remover_sessao(self):
        """Remove a sessão atual do banco de dados ao fechar."""
        try:
            with session_scope() as db_session:
                logging.info("Removendo sessão: ID %s", self.session_id)
                db_session.query(SystemControl).filter_by(key=self.session_id).delete(
                    synchronize_session=False
                )
        except SQLAlchemyError as e:
            logging.error("Erro ao remover sessão: %s", e)
        finally:
            if self.heartbeat_timer:
                self.heartbeat_timer.cancel()

    def atualizar_heartbeat_sessao(self):
        """Atualiza o timestamp da sessão ativa de forma otimizada para múltiplos usuários."""
        current_time = time.time()

        if current_time - self.last_heartbeat < self.heartbeat_interval:
            self._schedule_next_heartbeat()
            return

        try:
            with session_scope() as db_session:
                updated_count = (
                    db_session.query(SystemControl)
                    .filter_by(key=self.session_id)
                    .update({"last_updated": datetime.now(timezone.utc)})
                )
                if updated_count > 0:
                    self.last_heartbeat = current_time
                    logging.debug(
                        "Heartbeat atualizado para sessão %s", self.session_id
                    )
                else:
                    logging.warning(
                        "Sessão %s não encontrada para heartbeat, reregistrando...",
                        self.session_id,
                    )
                    self.registrar_sessao()
                    self.last_heartbeat = current_time
        except SQLAlchemyError as e:
            logging.error("Erro ao atualizar heartbeat da sessão: %s", e)
        finally:
            self._schedule_next_heartbeat()

    def _schedule_next_heartbeat(self):
        """Agenda a proxima execução do heartbeat de forma segura."""
        with self._lock:
            if self.heartbeat_timer:
                self.heartbeat_timer.cancel()
            self.heartbeat_timer = Timer(
                self.heartbeat_interval, self.atualizar_heartbeat_sessao
            )
            self.heartbeat_timer.daemon = True
            self.heartbeat_timer.start()

    def iniciar_heartbeat_automatico(self):
        """Inicia o sistema de heartbeat automático."""
        self.atualizar_heartbeat_sessao()

    def parar_heartbeat(self):
        """Para o sistema de heartbeat."""
        with self._lock:
            if self.heartbeat_timer:
                self.heartbeat_timer.cancel()
                self.heartbeat_timer = None

    @staticmethod
    def obter_comando_sistema() -> Optional[str]:
        """Busca no banco e retorna o comando atual do sistema ('SHUTDOWN', 'NONE', etc.)."""
        try:
            with session_scope() as db_session:
                if not db_session:
                    return None
                cmd_entry = (
                    db_session.query(SystemControl).filter_by(key="UPDATE_CMD").first()
                )
                return str(cmd_entry.value) if cmd_entry and cmd_entry.value else None
        except SQLAlchemyError as e:
            logging.error("Erro ao obter comando do sistema: %s", e)
            return None

    @staticmethod
    def definir_comando_sistema(comando: str):
        """Define um comando do sistema (ex: 'SHUTDOWN', 'UPDATE', etc.)."""
        try:
            with session_scope() as db_session:
                if not db_session:
                    return
                cmd_entry = (
                    db_session.query(SystemControl).filter_by(key="SYSTEM_CMD").first()
                )
                if cmd_entry:
                    cmd_entry.value = comando
                    cmd_entry.last_updated = datetime.now(timezone.utc)
                else:
                    novo_comando = SystemControl(
                        type="COMMAND",
                        key="SYSTEM_CMD",
                        value=comando,
                        last_updated=datetime.now(timezone.utc),
                    )
                    db_session.add(novo_comando)

                logging.info("Comando do sistema definido: %s", comando)
        except SQLAlchemyError as e:
            logging.error("Erro ao definir comando do sistema: %s", e)

    @staticmethod
    def obter_sessoes_ativas():
        """Retorna lista de todas as sessões ativas."""
        try:
            with session_scope() as db_session:
                if not db_session:
                    return []
                sessoes = (
                    db_session.query(SystemControl)
                    .filter_by(type="SESSION")
                    .order_by(SystemControl.last_updated.desc())
                    .all()
                )

                resultado = []
                for sessao in sessoes:
                    resultado.append(
                        {
                            "session_id": sessao.key,
                            "usuario": "Sistema",  # Pode ser expandido para incluir usuário
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
            return []

    # ... (restante dos métodos estáticos adaptados com with session_scope() ...)
    @staticmethod
    def limpar_comando_sistema():
        """Limpa o comando do sistema."""
        try:
            with session_scope() as db_session:
                if not db_session:
                    return
                cmd_entry = (
                    db_session.query(SystemControl).filter_by(key="SYSTEM_CMD").first()
                )
                if cmd_entry:
                    db_session.delete(cmd_entry)
                    logging.info("Comando do sistema limpo")
        except SQLAlchemyError as e:
            logging.error("Erro ao limpar comando do sistema: %s", e)

    @staticmethod
    def verificar_comando_shutdown() -> bool:
        """Verifica se existe comando de shutdown pendente."""
        try:
            with session_scope() as db_session:
                if not db_session:
                    return False
                cmd_entry = (
                    db_session.query(SystemControl).filter_by(key="SYSTEM_CMD").first()
                )
                return cmd_entry and cmd_entry.value == "SHUTDOWN"
        except SQLAlchemyError as e:
            logging.error("Erro ao verificar comando shutdown: %s", e)
            return False


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


def obter_comando_sistema() -> Optional[str]:
    """Busca no banco e retorna o comando atual do sistema."""
    return SessionManager.obter_comando_sistema()


def definir_comando_sistema(comando: str):
    """Define um comando do sistema (ex: 'SHUTDOWN', 'UPDATE', etc.)."""
    return SessionManager.definir_comando_sistema(comando)


def obter_sessoes_ativas():
    """Retorna lista de todas as sessões ativas."""
    return SessionManager.obter_sessoes_ativas()


def limpar_comando_sistema():
    """Limpa o comando do sistema."""
    return SessionManager.limpar_comando_sistema()


def verificar_comando_shutdown() -> bool:
    """Verifica se existe comando de shutdown pendente."""
    return SessionManager.verificar_comando_shutdown()


# Variáveis de compatibilidade
SESSION_ID = session_manager.session_id
