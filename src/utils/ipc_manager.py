"""Módulo para Gerenciamento de Comunicação entre Processos (IPC) via sistema de arquivos.

Responsável por:
- Criar e gerenciar um diretório de tempo de execução oculto.
- Manipular arquivos de sessão (criar, remover, verificar atividade).
- Manipular arquivos de comando (criar, verificar, remover).
"""

import ctypes
import json
import logging
import os
import shutil
import time
from datetime import datetime
from typing import Any, Dict, List

from src.utils.utilitarios import CACHE_DIR, COMMAND_DIR, RUNTIME_DIR, SESSION_DIR

FILE_ATTRIBUTE_HIDDEN = 0x02


# --- Funções de Nível de Sistema Operacional ---


def _hide_path(path: str) -> None:
    """Define o atributo 'oculto' em um arquivo ou diretório no Windows.

    No Linux/macOS, arquivos que começam com '.' já são ocultos por padrão.
    """
    if os.name == "nt":
        try:
            # Constante para atributo de arquivo oculto no Windows
            ret = ctypes.windll.kernel32.SetFileAttributesW(path, FILE_ATTRIBUTE_HIDDEN)
            if ret:
                logging.info("Diretório de execução '%s' ocultado.", path)
            else:
                logging.warning(
                    "Não foi possível definir o atributo oculto em '%s'.", path
                )
        except (AttributeError, OSError) as e:
            logging.error("Erro ao tentar ocultar o diretório: %s", e)


# Arquivos de Sinalização (Signal Files) para atualizações em tempo real
SIGNAL_DIR = os.path.join(RUNTIME_DIR, "signals")
AVISOS_SIGNAL_FILE = os.path.join(SIGNAL_DIR, "avisos_updated.signal")


def ensure_ipc_dirs_exist() -> None:
    """
    Garante que os diretórios de IPC existam e tenta ocultá-los.
    """
    try:
        if not os.path.exists(RUNTIME_DIR):
            os.makedirs(SESSION_DIR, exist_ok=True)
            os.makedirs(COMMAND_DIR, exist_ok=True)
            os.makedirs(CACHE_DIR, exist_ok=True)
            os.makedirs(SIGNAL_DIR, exist_ok=True)
            _hide_path(RUNTIME_DIR)
        else:
            os.makedirs(SESSION_DIR, exist_ok=True)
            os.makedirs(COMMAND_DIR, exist_ok=True)
            os.makedirs(CACHE_DIR, exist_ok=True)
            os.makedirs(SIGNAL_DIR, exist_ok=True)

        # Garante a existência do arquivo de sinal
        if not os.path.exists(AVISOS_SIGNAL_FILE):
            with open(AVISOS_SIGNAL_FILE, 'w') as f:
                f.write(str(time.time()))

    except OSError as e:
        logging.critical("Não foi possível criar os diretórios de IPC: %s", e)
        raise


def send_update_signal(signal_file: str) -> None:
    """Atualiza o timestamp do arquivo de sinal para notificar listeners."""
    try:
        if not os.path.exists(signal_file):
            with open(signal_file, 'w') as f:
                f.write(str(time.time()))
        else:
            os.utime(signal_file, None)
    except OSError as e:
        logging.error("Erro ao enviar sinal de atualização em '%s': %s", signal_file, e)


# --- Gerenciamento de Sessões ---


def create_session_file(session_id: str, hostname: str) -> None:
    """Cria um arquivo para representar uma sessão ativa, armazenando o hostname."""
    session_file = os.path.join(SESSION_DIR, f"{session_id}.session")
    data = {"hostname": hostname}
    try:
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
        logging.info("Arquivo de sessão criado: %s", session_file)
    except IOError as e:
        logging.error("Erro ao criar arquivo de sessão '%s': %s", session_id, e)


def remove_session_file(session_id: str) -> None:
    """Remove um arquivo de sessão."""
    session_file = os.path.join(SESSION_DIR, f"{session_id}.session")
    if os.path.exists(session_file):
        try:
            os.remove(session_file)
            logging.info("Arquivo de sessão removido: %s", session_file)
        except OSError as e:
            logging.error("Erro ao remover arquivo de sessão '%s': %s", session_id, e)


def touch_session_file(session_id: str, hostname: str) -> None:
    """
    Atualiza o timestamp de modificação de um arquivo de sessão (heartbeat).
    Recria o arquivo se ele não existir.
    """
    session_file = os.path.join(SESSION_DIR, f"{session_id}.session")
    try:
        # os.utime é mais eficiente que reescrever o arquivo para o heartbeat
        os.utime(session_file, None)
    except OSError:
        # Se o arquivo não existir (ex: foi limpo), recria com os dados corretos
        logging.warning(
            "Arquivo de sessão '%s' não encontrado para heartbeat. Recriando.",
            session_id,
        )
        create_session_file(session_id, hostname)


def get_active_sessions() -> List[Dict[str, Any]]:
    """
    Retorna uma lista de dicionários com detalhes das sessões ativas.
    """
    sessions = []
    if not os.path.isdir(SESSION_DIR):
        return []

    try:
        session_files = [f for f in os.listdir(SESSION_DIR) if f.endswith(".session")]
        for filename in session_files:
            session_id = filename.replace(".session", "")
            filepath = os.path.join(SESSION_DIR, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    hostname = "N/A"  # Valor padrão

                    # ** INÍCIO DA CORREÇÃO **
                    # Verifica se o dado lido é um dicionário (novo formato)
                    if isinstance(data, dict):
                        hostname = data.get("hostname", "Desconhecido")
                    # Se não for, ignora o conteúdo e usa o valor padrão "N/A",
                    # evitando o erro ao tratar arquivos de formato antigo.
                    # ** FIM DA CORREÇÃO **

                last_modified_timestamp = os.path.getmtime(filepath)
                last_updated = datetime.fromtimestamp(last_modified_timestamp).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                sessions.append(
                    {
                        "session_id": session_id,
                        "hostname": hostname,
                        "last_updated": last_updated,
                    }
                )
            except (json.JSONDecodeError, FileNotFoundError, OSError) as e:
                logging.warning(
                    "Não foi possível ler o arquivo de sessão '%s': %s", filename, e
                )
                continue
        return sessions
    except OSError as e:
        logging.error("Erro ao listar sessões ativas: %s", e)
        return []


def cleanup_inactive_sessions(timeout_seconds: int = 120) -> None:
    """Remove arquivos de sessão que não foram atualizados dentro do timeout."""
    # Chama get_active_sessions para obter os IDs, não precisa dos detalhes aqui
    active_session_ids = [s["session_id"] for s in get_active_sessions()]
    if not active_session_ids:
        return

    logging.info("Limpando sessões inativas...")
    now = time.time()
    for session_id in active_session_ids:
        session_file = os.path.join(SESSION_DIR, f"{session_id}.session")
        try:
            last_modified = os.path.getmtime(session_file)
            if (now - last_modified) > timeout_seconds:
                logging.warning(
                    "Removendo sessão inativa (ID: %s) - Última atividade: %.2f s atrás.",
                    session_id,
                    now - last_modified,
                )
                remove_session_file(session_id)
        except FileNotFoundError:
            # A sessão pode ter sido fechada normalmente entre a listagem e aqui
            continue
        except OSError as e:
            logging.error("Erro ao verificar sessão inativa '%s': %s", session_id, e)
    logging.info("Limpeza de sessões inativas concluída.")


# --- Gerenciamento de Comandos ---

_COMMAND_MAP = {
    "SHUTDOWN": "shutdown.cmd",
}


def create_command_file(command: str) -> None:
    """Cria um arquivo de comando para sinalizar uma ação a todas as instâncias."""
    command_filename = _COMMAND_MAP.get(command.upper())
    if not command_filename:
        logging.error("Comando desconhecido: %s", command)
        return

    command_file = os.path.join(COMMAND_DIR, command_filename)
    try:
        with open(command_file, "w", encoding="utf-8") as f:
            f.write("active")
        logging.info("Arquivo de comando '%s' criado.", command)
    except IOError as e:
        logging.error("Erro ao criar arquivo de comando '%s': %s", command, e)


def check_for_command(command: str) -> bool:
    """Verifica se um arquivo de comando existe."""
    command_filename = _COMMAND_MAP.get(command.upper())
    if not command_filename:
        return False
    return os.path.exists(os.path.join(COMMAND_DIR, command_filename))


def clear_command(command: str) -> None:
    """Remove um arquivo de comando."""
    command_filename = _COMMAND_MAP.get(command.upper())
    if not command_filename:
        return

    command_file = os.path.join(COMMAND_DIR, command_filename)
    if os.path.exists(command_file):
        try:
            os.remove(command_file)
            logging.info("Arquivo de comando '%s' removido.", command)
        except OSError as e:
            logging.error("Erro ao remover arquivo de comando '%s': %s", command, e)


def clear_all_commands() -> None:
    """Remove todos os arquivos de comando, limpando o diretório."""
    if os.path.isdir(COMMAND_DIR):
        try:
            shutil.rmtree(COMMAND_DIR)
            os.makedirs(COMMAND_DIR, exist_ok=True)
            logging.info("Todos os arquivos de comando foram limpos.")
        except OSError as e:
            logging.error("Erro ao limpar diretório de comandos: %s", e)
