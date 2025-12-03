"""Conversão DWG para DWG 2013 com suporte a substituição do original.

Este módulo isolado concentra a lógica específica da conversão DWG->DWG 2013,
reduzindo o tamanho de converter_worker.py.
"""

import logging
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
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
    nome_dwg_2013 = nome_base + ".dwg"

    if not oda_executable:
        return (
            False,
            "ODA Converter não está configurado corretamente.",
            None,
        )

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
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

            run_trusted_command(
                command,
                description="ODA Converter DWG->DWG 2013",
                capture_output=True,
                timeout=300,
                startupinfo=_prepare_startupinfo(),
                text=True,
                encoding="utf-8",
            )

            # Procura pelo arquivo DWG convertido
            expected_dwg = Path(temp_dir, nome_dwg_2013)
            arquivo_convertido = None

            if expected_dwg.exists():
                arquivo_convertido = str(expected_dwg)
            else:
                # Fallback: procura qualquer arquivo DWG gerado
                fallback = next(Path(temp_dir).glob("*.dwg"), None)
                if fallback:
                    arquivo_convertido = str(fallback)

            if not arquivo_convertido:
                logging.error("FALHA: Arquivo DWG 2013 não foi criado.")
                return (
                    False,
                    "Arquivo DWG 2013 não foi criado.",
                    None,
                )

            # Se substituir_original está ativo, substitui o original
            if substituir_original:
                path_destino = path_origem
                path_backup = None

                if ensure_unique_path_func:
                    path_backup = ensure_unique_path_func(
                        os.path.join(pasta_destino, f"{nome_base}.bak")
                    )
                else:
                    path_backup = os.path.join(
                        pasta_destino, f"{nome_base}.bak"
                    )

                try:
                    # Move o arquivo original para a pasta de destino como backup
                    shutil.move(path_origem, path_backup)
                    # Move o arquivo convertido para o local do original
                    shutil.move(arquivo_convertido, path_destino)
                    mensagem = (
                        f"Conversão bem-sucedida. "
                        f"Backup salvo como {os.path.basename(path_backup)}"
                    )
                    return (
                        True,
                        mensagem,
                        [path_destino, path_backup],
                    )
                except OSError as exc:
                    logging.error(
                        "Erro ao substituir arquivo original %s.",
                        nome_arquivo,
                        exc_info=True,
                    )
                    # Se algo falhar, tentar mover para a pasta de destino
                    path_destino_fallback = None

                    if ensure_unique_path_func:
                        path_destino_fallback = ensure_unique_path_func(
                            os.path.join(pasta_destino, nome_dwg_2013)
                        )
                    else:
                        path_destino_fallback = os.path.join(
                            pasta_destino, nome_dwg_2013
                        )

                    shutil.move(arquivo_convertido, path_destino_fallback)
                    basename = os.path.basename(path_destino_fallback)
                    msg = (
                        f"Falha ao substituir original: {str(exc)}. "
                        f"Arquivo salvo em {basename}"
                    )
                    return (False, msg, [path_destino_fallback])

            # Modo padrão: salva na pasta de destino
            path_destino = None

            if ensure_unique_path_func:
                path_destino = ensure_unique_path_func(
                    os.path.join(pasta_destino, nome_dwg_2013)
                )
            else:
                path_destino = os.path.join(pasta_destino, nome_dwg_2013)

            shutil.move(arquivo_convertido, path_destino)
            return (
                True,
                "Conversão bem-sucedida",
                [path_destino],
            )

    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
    ) as exc:
        logging.error(
            "FALHA na conversão DWG->DWG 2013 para %s.",
            nome_arquivo,
            exc_info=True,
        )
        msg = f"Falha na conversão: {getattr(exc, 'stderr', exc)}"
        return (False, msg, None)
    except OSError as exc:
        logging.error(
            "Erro de arquivo na conversão de %s.",
            nome_arquivo,
            exc_info=True,
        )
        return (False, str(exc), None)
