"""Conversão de PDF para DXF.

Este módulo concentra a lógica de conversão de PDF para DXF,
utilizando o Inkscape como ferramenta de conversão.
"""

import logging
import os
import shutil
import subprocess
import sys
import tempfile
from typing import Optional

from src.utils.utilitarios import run_trusted_command


def _prepare_startupinfo() -> Optional[subprocess.STARTUPINFO]:
    """Cria o objeto STARTUPINFO configurado para ocultar janelas no Windows."""
    if sys.platform != "win32":
        return None

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    return startupinfo


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

                if prepare_pdf_pages_func:
                    page_sources, _, use_page_numbers = (
                        prepare_pdf_pages_func(temp_pdf_path, nome_arquivo)
                    )
                else:
                    page_sources = [temp_pdf_path]
                    use_page_numbers = False

                arquivos_gerados: list[str] = []

                for page_index, page_source in enumerate(page_sources, start=1):
                    temp_dxf_path = os.path.join(
                        temp_dir, f"saida_{page_index}.dxf"
                    )
                    nome_destino = (
                        f"{nome_base}.dxf"
                        if len(page_sources) == 1
                        else f"{nome_base}_p{page_index}.dxf"
                    )

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

                    if os.path.exists(temp_dxf_path):
                        path_destino = None
                        if ensure_unique_path_func:
                            path_destino = ensure_unique_path_func(
                                os.path.join(pasta_destino, nome_destino)
                            )
                        else:
                            path_destino = os.path.join(
                                pasta_destino, nome_destino
                            )

                        shutil.move(temp_dxf_path, path_destino)
                        arquivos_gerados.append(path_destino)

                if arquivos_gerados:
                    msg = (
                        f"{len(arquivos_gerados)} páginas convertidas: "
                        + ", ".join(
                            os.path.basename(p) for p in arquivos_gerados
                        )
                    )
                    return (True, msg, arquivos_gerados)
                else:
                    return (False, "Nenhuma página foi convertida.", None)

            except (
                subprocess.CalledProcessError,
                subprocess.TimeoutExpired,
                FileNotFoundError,
            ) as exc:
                logging.error(
                    "FALHA na conversão de %s.",
                    nome_arquivo,
                    exc_info=True,
                )
                error_output = "Comando falhou."
                if hasattr(exc, "stderr") and exc.stderr:
                    error_output = exc.stderr
                elif hasattr(exc, "stdout") and exc.stdout:
                    error_output = exc.stdout
                else:
                    error_output = str(exc)

                logging.error(
                    "Detalhes do erro do subprocesso: %s",
                    error_output,
                )
                return (False, error_output, None)

    except (IOError, OSError) as exc:
        logging.error(
            "Erro de arquivo na conversão de %s.",
            nome_arquivo,
            exc_info=True,
        )
        return (False, str(exc), None)
