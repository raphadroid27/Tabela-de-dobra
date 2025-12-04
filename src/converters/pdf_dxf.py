"""Conversão de PDF para DXF.

Este módulo concentra a lógica de conversão de PDF para DXF,
utilizando o Inkscape como ferramenta de conversão.
"""

import os
import shutil
import subprocess
import tempfile
from typing import Optional

from src.converters.common import (
    build_subprocess_failure,
    get_file_destination,
    log_os_error,
)
from src.utils.utilitarios import run_trusted_command

SUBPROCESS_ERRORS = (
    subprocess.CalledProcessError,
    subprocess.TimeoutExpired,
    FileNotFoundError,
)


def _processar_pagina_pdf(
    page_index: int,
    page_source: str,
    temp_dir: str,
    inkscape_executable: str,
    use_page_numbers: bool,
) -> Optional[str]:
    """Processa uma página PDF para DXF.

    Returns:
        Caminho do arquivo DXF gerado ou None se falhar
    """
    temp_dxf_path = os.path.join(temp_dir, f"saida_{page_index}.dxf")

    command = [
        inkscape_executable,
        page_source,
        f"--export-filename={temp_dxf_path}",
        "--export-type=dxf",
        "--export-overwrite",
        "--export-area-drawing",
        "--pdf-poppler",
    ]
    if use_page_numbers:
        command.append(f"--pdf-page={page_index}")

    run_trusted_command(
        command,
        description="Inkscape PDF->DXF",
        capture_output=True,
        text=True,
        timeout=240,
        encoding="utf-8",
    )

    return temp_dxf_path if os.path.exists(temp_dxf_path) else None


def _obter_nome_destino(nome_base: str, page_index: int, total_pages: int) -> str:
    """Determina o nome do arquivo de destino."""
    if total_pages == 1:
        return f"{nome_base}.dxf"
    return f"{nome_base}_p{page_index}.dxf"


def _processar_paginas_pdf(
    page_sources: list,
    config: dict,
) -> list[str]:
    """Processa todas as páginas do PDF.

    Args:
        page_sources: Lista de caminhos das páginas PDF
        config: Dicionário com {temp_dir, inkscape_executable, use_page_numbers,
                nome_base, pasta_destino, ensure_unique_path_func}

    Returns:
        Lista de arquivos gerados
    """
    arquivos_gerados: list[str] = []

    for page_index, page_source in enumerate(page_sources, start=1):
        temp_dxf_path = _processar_pagina_pdf(
            page_index,
            page_source,
            config["temp_dir"],
            config["inkscape_executable"],
            config["use_page_numbers"],
        )

        if not temp_dxf_path:
            continue

        nome_destino = _obter_nome_destino(
            config["nome_base"],
            page_index,
            len(page_sources),
        )
        path_destino = get_file_destination(
            config["pasta_destino"],
            nome_destino,
            config.get("ensure_unique_path_func"),
        )

        shutil.move(temp_dxf_path, path_destino)
        arquivos_gerados.append(path_destino)

    return arquivos_gerados


def _preparar_config_pdf(
    temp_dir: str,
    temp_pdf_path: str,
    params: dict,
) -> tuple[list, dict]:
    """Prepara configuração e obtém page_sources.

    Args:
        temp_dir: Diretório temporário
        temp_pdf_path: Caminho do PDF temporário
        params: Dict com {inkscape_executable, nome_base, pasta_destino,
                prepare_pdf_pages_func, nome_arquivo, ensure_unique_path_func}

    Returns:
        Tuple (page_sources, config)
    """
    if params.get("prepare_pdf_pages_func"):
        page_sources, _, use_page_numbers = params["prepare_pdf_pages_func"](
            temp_pdf_path,
            params["nome_arquivo"],
        )
    else:
        page_sources = [temp_pdf_path]
        use_page_numbers = False

    config = {
        "temp_dir": temp_dir,
        "inkscape_executable": params["inkscape_executable"],
        "use_page_numbers": use_page_numbers,
        "nome_base": params["nome_base"],
        "pasta_destino": params["pasta_destino"],
        "ensure_unique_path_func": params.get("ensure_unique_path_func"),
    }

    return page_sources, config


def converter_pdf_para_dxf(
    path_origem: str,
    pasta_destino: str,
    inkscape_executable: str,
    prepare_pdf_pages_func=None,
    ensure_unique_path_func=None,
) -> tuple[bool, str, Optional[list[str]]]:
    """Converte um arquivo PDF para DXF (uma página por arquivo).

    Args:
        path_origem: Caminho do arquivo PDF original
        pasta_destino: Pasta onde salvar os resultados
        inkscape_executable: Caminho do executável Inkscape
        prepare_pdf_pages_func: Função para preparar páginas do PDF
        ensure_unique_path_func: Função para garantir caminhos únicos

    Returns:
        Tuple (sucesso, mensagem, lista_de_arquivos)
    """
    nome_arquivo = os.path.basename(path_origem)
    nome_base = os.path.splitext(nome_arquivo)[0]

    if not inkscape_executable:
        return (False, "Inkscape não está configurado corretamente.", None)

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                temp_pdf_path = os.path.join(temp_dir, "entrada.pdf")
                shutil.copy(path_origem, temp_pdf_path)

                page_sources, config = _preparar_config_pdf(
                    temp_dir,
                    temp_pdf_path,
                    {
                        "inkscape_executable": inkscape_executable,
                        "nome_base": nome_base,
                        "pasta_destino": pasta_destino,
                        "prepare_pdf_pages_func": prepare_pdf_pages_func,
                        "nome_arquivo": nome_arquivo,
                        "ensure_unique_path_func": ensure_unique_path_func,
                    },
                )

                arquivos_gerados = _processar_paginas_pdf(
                    page_sources,
                    config,
                )

                if arquivos_gerados:
                    msg = f"{len(arquivos_gerados)} páginas convertidas: " + ", ".join(
                        os.path.basename(p) for p in arquivos_gerados
                    )
                    return (True, msg, arquivos_gerados)

                return (False, "Nenhuma página foi convertida.", None)

            except SUBPROCESS_ERRORS as exc:
                return build_subprocess_failure(exc, nome_arquivo, "conversão PDF->DXF")

    except (IOError, OSError) as exc:
        return (False, log_os_error(exc, nome_arquivo), None)
