"""Conversão DWG para DWG 2013 com suporte a substituição do original.

Este módulo isolado concentra a lógica específica da conversão DWG->DWG 2013,
reduzindo o tamanho de converter_worker.py.
"""

import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from src.forms.common.converters_common import (
    get_file_destination,
    handle_subprocess_error,
    log_os_error,
    run_oda_command,
)


def _executar_oda_converter(
    path_origem: str,
    oda_executable: str,
    nome_arquivo: str,
    temp_dir: str,
) -> Optional[str]:
    """Executa ODA Converter e retorna caminho do arquivo convertido.

    Returns:
        Caminho do arquivo convertido ou None se falhar
    """
    nome_base = os.path.splitext(nome_arquivo)[0]
    nome_dwg_2013 = nome_base + ".dwg"

    command = [
        oda_executable,
        os.path.dirname(path_origem),
        temp_dir,
        "ACAD2013",
        "DWG",
        "0",
        "1",
        nome_arquivo,
    ]

    run_oda_command(command, "ODA Converter DWG->DWG 2013")

    expected_dwg = Path(temp_dir, nome_dwg_2013)
    if expected_dwg.exists():
        return str(expected_dwg)

    # Fallback: qualquer arquivo DXF gerado
    fallback = next(Path(temp_dir).glob("*.dwg"), None)
    return str(fallback) if fallback else None


def _substituir_arquivo_original(
    arquivo_convertido: str,
    path_origem: str,
    pasta_destino: str,
    nome_base: str,
    ensure_unique_path_func=None,
) -> tuple[bool, str, Optional[list[str]]]:
    """Substitui arquivo original com backup .bak.

    Returns:
        Tuple (sucesso, mensagem, lista_arquivos)
    """
    path_backup = get_file_destination(
        pasta_destino,
        f"{nome_base}.bak",
        ensure_unique_path_func,
    )

    try:
        shutil.move(path_origem, path_backup)
        shutil.move(arquivo_convertido, path_origem)
        msg = (
            f"Conversão bem-sucedida. "
            f"Backup salvo como {os.path.basename(path_backup)}"
        )
        return (True, msg, [path_origem, path_backup])
    except OSError as exc:
        logging.error(
            "Erro ao substituir arquivo original %s.",
            os.path.basename(path_origem),
            exc_info=True,
        )
        # Fallback: salvar na pasta de destino
        nome_dwg_2013 = nome_base + ".dwg"
        path_fallback = get_file_destination(
            pasta_destino,
            nome_dwg_2013,
            ensure_unique_path_func,
        )
        shutil.move(arquivo_convertido, path_fallback)
        msg = (
            f"Falha ao substituir original: {str(exc)}. "
            f"Arquivo salvo em {os.path.basename(path_fallback)}"
        )
        return (False, msg, [path_fallback])


def _salvar_em_pasta_destino(
    arquivo_convertido: str,
    pasta_destino: str,
    nome_base: str,
    ensure_unique_path_func=None,
) -> tuple[bool, str, list[str]]:
    """Salva arquivo convertido na pasta de destino.

    Returns:
        Tuple (sucesso, mensagem, lista_arquivos)
    """
    nome_dwg_2013 = nome_base + ".dwg"
    path_destino = get_file_destination(
        pasta_destino,
        nome_dwg_2013,
        ensure_unique_path_func,
    )
    shutil.move(arquivo_convertido, path_destino)
    return (True, "Conversão bem-sucedida", [path_destino])


def converter_dwg_para_dwg_2013(
    path_origem: str,
    pasta_destino: str,
    oda_executable: str,
    substituir_original: bool = False,
    ensure_unique_path_func=None,
) -> tuple[bool, str, Optional[list[str]]]:
    """Converte DWG para DWG versão 2013.

    Args:
        path_origem: Caminho do arquivo DWG original
        pasta_destino: Pasta onde salvar o resultado
        oda_executable: Caminho do executável ODA Converter
        substituir_original: Se True, substitui o original com backup .bak
        ensure_unique_path_func: Função para garantir caminhos únicos

    Returns:
        Tuple (sucesso, mensagem, lista_de_arquivos_criados)
    """
    nome_arquivo = os.path.basename(path_origem)
    nome_base = os.path.splitext(nome_arquivo)[0]

    if not oda_executable:
        return (
            False,
            "ODA Converter não está configurado corretamente.",
            None,
        )

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            arquivo_convertido = _executar_oda_converter(
                path_origem,
                oda_executable,
                nome_arquivo,
                temp_dir,
            )

            if not arquivo_convertido:
                logging.error("FALHA: Arquivo DWG 2013 não foi criado.")
                return (
                    False,
                    "Arquivo DWG 2013 não foi criado.",
                    None,
                )

            if substituir_original:
                return _substituir_arquivo_original(
                    arquivo_convertido,
                    path_origem,
                    pasta_destino,
                    nome_base,
                    ensure_unique_path_func,
                )

            return _salvar_em_pasta_destino(
                arquivo_convertido,
                pasta_destino,
                nome_base,
                ensure_unique_path_func,
            )

    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
    ) as exc:
        msg = handle_subprocess_error(
            exc,
            nome_arquivo,
            "conversão DWG->DWG 2013",
        )
        return (False, msg, None)
    except OSError as exc:
        return (False, log_os_error(exc, nome_arquivo), None)
