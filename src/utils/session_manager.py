"""
Gerenciamento de sessões do sistema e comandos, usando comunicação
baseada em arquivos (IPC) para evitar concorrência no banco de dados.
"""

import logging
import socket
import time
import uuid
from typing import Callable, Optional

from src.utils import ipc_manager

# Gera um ID único para cada instância da aplicação em execução.
SESSION_ID = str(uuid.uuid4())
HOSTNAME = socket.gethostname()


def registrar_sessao():
    """Registra a sessão atual criando seu arquivo de sessão com o hostname."""
    logging.info(
        "Registrando nova sessão via arquivo: ID %s para host %s",
        SESSION_ID,
        HOSTNAME,
    )
    ipc_manager.create_session_file(SESSION_ID, HOSTNAME)


def remover_sessao():
    """Remove a sessão atual do sistema de arquivos ao fechar."""
    logging.info("Removendo sessão via arquivo: ID %s", SESSION_ID)
    ipc_manager.remove_session_file(SESSION_ID)


def limpar_sessoes_inativas(timeout_minutos: int = 2):
    """
    Verifica e remove arquivos de sessão que não foram atualizados (heartbeat)
    dentro do tempo limite especificado.
    """
    ipc_manager.cleanup_inactive_sessions(timeout_seconds=timeout_minutos * 60)


def atualizar_heartbeat_sessao():
    """Atualiza o timestamp do arquivo da sessão para indicar que está online."""
    ipc_manager.touch_session_file(SESSION_ID, HOSTNAME)


def obter_sessoes_ativas():
    """Retorna uma lista de todas as sessões ativas com detalhes."""
    return ipc_manager.get_active_sessions()


def verificar_comando_sistema() -> bool:
    """
    Verifica se há um comando de sistema para desligar a aplicação
    procurando por um arquivo de comando.
    """
    if ipc_manager.check_for_command("SHUTDOWN"):
        logging.warning(
            "Comando SHUTDOWN via arquivo recebido. Sinalizando para encerrar."
        )
        return True
    return False


def force_shutdown_all_instances(
    progress_callback: Optional[Callable[[int], None]] = None,
) -> bool:
    """
    Força o encerramento de todas as instâncias criando um arquivo de comando 'SHUTDOWN'.

    Args:
        progress_callback: Função opcional para notificar o número de sessões ativas restantes.

    Returns:
        True se todas as instâncias fecharam, False em caso de timeout.
    """
    logging.info("Enviando comando de encerramento via arquivo...")
    ipc_manager.create_command_file("SHUTDOWN")

    try:
        start_time = time.time()
        # Timeout de 60 segundos
        while (time.time() - start_time) < 60:
            # get_active_sessions agora retorna a lista detalhada
            active_sessions = ipc_manager.get_active_sessions()
            num_sessions = len(active_sessions)

            if progress_callback:
                progress_callback(num_sessions)

            if num_sessions == 0:
                logging.info("Todas as instâncias foram fechadas.")
                if progress_callback:
                    progress_callback(0)
                return True

            time.sleep(2)  # Aguarda 2 segundos antes de verificar novamente

        logging.error("Timeout! As instâncias não fecharam a tempo.")
        return False
    finally:
        # Garante que o arquivo de comando seja limpo ao final do processo
        logging.info("Limpando arquivo de comando SHUTDOWN.")
        ipc_manager.clear_command("SHUTDOWN")
