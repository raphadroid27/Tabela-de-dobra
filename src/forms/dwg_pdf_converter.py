"""Conversão de DWG para PDF.

Este módulo concentra a lógica de conversão de DWG para PDF,
utilizando o ODA Converter (DWG->DXF) e depois renderizando para PDF.
"""

import logging
import os
import subprocess
import sys
import tempfile
from typing import Optional


def _prepare_startupinfo() -> Optional[subprocess.STARTUPINFO]:
    """Cria o objeto STARTUPINFO configurado para ocultar janelas no Windows."""
    if sys.platform != "win32":
        return None

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    return startupinfo


def converter_dwg_para_pdf(
    path_origem: str,
    generate_dxf_func,
    convert_dxf_to_pdf_func,
) -> tuple[bool, str, Optional[str]]:
    """Converte DWG para PDF em duas etapas: DWG -> DXF, depois DXF -> PDF.

    Args:
        path_origem: Caminho do arquivo DWG original
        generate_dxf_func: Função para gerar DXF intermediário
        convert_dxf_to_pdf_func: Função para converter DXF para PDF

    Returns:
        Tuple (sucesso, mensagem, caminho_arquivo_resultado)
    """
    nome_arquivo = os.path.basename(path_origem)

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            path_dxf_temp = os.path.join(temp_dir, "intermediario.dxf")

            # Etapa 1: Gerar DXF temporário
            sucesso_dxf, msg_dxf = generate_dxf_func(
                path_origem, nome_arquivo, path_dxf_temp
            )
            if not sucesso_dxf:
                return (False, msg_dxf, None)

            # Etapa 2: Converter DXF para PDF
            sucesso_pdf, msg_pdf, path_pdf = convert_dxf_to_pdf_func(
                path_dxf_temp, path_origem
            )
            return (sucesso_pdf, msg_pdf, path_pdf)

    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
    ) as exc:
        logging.error(
            "FALHA na etapa DWG->DXF para %s.",
            nome_arquivo,
            exc_info=True,
        )
        msg = f"Falha na etapa DWG->DXF: {getattr(exc, 'stderr', exc)}"
        return (False, msg, None)
    except OSError as exc:
        logging.error(
            "Erro de arquivo na conversão de %s.",
            nome_arquivo,
            exc_info=True,
        )
        return (False, str(exc), None)
