"""Utilitários compartilhados para módulos de conversão.

Concentra funções comuns usadas por múltiplos conversores,
eliminando duplicação de código e melhorando manutenibilidade.
"""

import logging
import os
import subprocess
import sys
from typing import Optional

from src.utils.utilitarios import run_trusted_command


def prepare_startupinfo() -> Optional[subprocess.STARTUPINFO]:
    """Cria o objeto STARTUPINFO configurado para ocultar janelas no Windows.

    Returns:
        subprocess.STARTUPINFO configurado para ocultar ou None em outros SOs.
    """
    if sys.platform != "win32":
        return None

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    return startupinfo


def get_file_destination(
    pasta_destino: str,
    nome_arquivo: str,
    ensure_unique_path_func=None,
) -> str:
    """Obtém o caminho de destino, garantindo unicidade se necessário.

    Args:
        pasta_destino: Pasta de destino base
        nome_arquivo: Nome do arquivo
        ensure_unique_path_func: Função para garantir caminhos únicos (opcional)

    Returns:
        Caminho completo do arquivo de destino
    """
    path_destino = os.path.join(pasta_destino, nome_arquivo)

    if ensure_unique_path_func:
        return ensure_unique_path_func(path_destino)

    return path_destino


def extract_error_message(exc: Exception) -> str:
    """Extrai mensagem de erro clara de uma exceção.

    Args:
        exc: Exceção a processar

    Returns:
        Mensagem de erro formatada
    """
    if hasattr(exc, "stderr") and exc.stderr:
        return exc.stderr
    if hasattr(exc, "stdout") and exc.stdout:
        return exc.stdout
    return str(exc)


def log_subprocess_error(
    exc: Exception,
    nome_arquivo: str,
    etapa: str,
) -> str:
    """Log estruturado de erro de subprocesso e retorna mensagem.

    Args:
        exc: Exceção capturada
        nome_arquivo: Nome do arquivo processado
        etapa: Descrição da etapa que falhou

    Returns:
        Mensagem de erro para retorno
    """
    logging.error(
        "FALHA na etapa %s para %s.",
        etapa,
        nome_arquivo,
        exc_info=True,
    )

    error_msg = extract_error_message(exc)
    if error_msg:
        logging.error(
            "Detalhes do erro do subprocesso: %s",
            error_msg,
        )

    return f"Falha na etapa {etapa}: {error_msg}"


def log_os_error(
    exc: OSError,
    nome_arquivo: str,
) -> str:
    """Log estruturado de erro de sistema de arquivos.

    Args:
        exc: Exceção OSError capturada
        nome_arquivo: Nome do arquivo processado

    Returns:
        Mensagem de erro para retorno
    """
    logging.error(
        "Erro de arquivo na conversão de %s.",
        nome_arquivo,
        exc_info=True,
    )
    return str(exc)


def handle_subprocess_error(
    exc: Exception,
    nome_arquivo: str,
    etapa: str = "conversão",
) -> str:
    """Trata e loga erros de subprocesso de forma centralizada.

    Args:
        exc: Exceção capturada
        nome_arquivo: Nome do arquivo sendo processado
        etapa: Descrição da etapa (padrão: 'conversão')

    Returns:
        Mensagem de erro para retorno
    """
    logging.error(
        "FALHA na %s para %s.",
        etapa,
        nome_arquivo,
        exc_info=True,
    )
    error_msg = extract_error_message(exc)
    if error_msg:
        logging.error("Detalhes do erro: %s", error_msg)
    return f"Falha na {etapa}: {error_msg}"


def build_subprocess_failure(
    exc: Exception,
    nome_arquivo: str,
    etapa: str,
) -> tuple[bool, str, None]:
    """Retorna tupla de falha padrão para erros de subprocesso."""

    msg = handle_subprocess_error(exc, nome_arquivo, etapa)
    return (False, msg, None)


def run_oda_command(command: list[str], description: str):
    """Executa o ODA Converter com parâmetros padrão."""

    return run_trusted_command(
        command,
        description=description,
        capture_output=True,
        timeout=300,
        startupinfo=prepare_startupinfo(),
        text=True,
        encoding="utf-8",
    )
