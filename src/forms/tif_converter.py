"""Conversão de TIF para PDF.

Este módulo concentra a lógica de conversão de arquivos TIF/TIFF para PDF,
utilizando a biblioteca Pillow.
"""

import logging
import os
from typing import Optional

from src.forms.common.converters_common import get_file_destination

try:
    from PIL import Image, ImageSequence, UnidentifiedImageError

    PIL_AVAILABLE = True
except ImportError:
    Image = None
    UnidentifiedImageError = None
    PIL_AVAILABLE = False


def converter_tif_para_pdf(
    path_origem: str,
    pasta_destino: str,
    ensure_unique_path_func=None,
) -> tuple[bool, str, Optional[str]]:
    """Converte um arquivo TIF para PDF.

    Args:
        path_origem: Caminho do arquivo TIF original
        pasta_destino: Pasta onde salvar o resultado
        ensure_unique_path_func: Função para garantir caminhos únicos

    Returns:
        Tuple (sucesso, mensagem, caminho_arquivo_resultado)
    """
    if not PIL_AVAILABLE or Image is None:
        return (False, "Biblioteca Pillow indisponível", None)

    nome_arquivo = os.path.basename(path_origem)
    nome_pdf = os.path.splitext(nome_arquivo)[0] + ".pdf"

    path_destino = get_file_destination(
        pasta_destino,
        nome_pdf,
        ensure_unique_path_func,
    )

    try:
        frames_rgb = []
        with Image.open(path_origem) as img:
            for frame in ImageSequence.Iterator(img):
                frames_rgb.append(frame.convert("RGB"))

        if not frames_rgb:
            raise UnidentifiedImageError("Arquivo TIF sem páginas utilizáveis.")

        primeira_pagina, *demais_paginas = frames_rgb
        save_kwargs = {
            "save_all": bool(demais_paginas),
            "append_images": demais_paginas,
            "optimize": True,
        }
        primeira_pagina.save(path_destino, "PDF", **save_kwargs)

        return (True, "Conversão bem-sucedida", path_destino)

    except (IOError, UnidentifiedImageError, OSError, MemoryError) as exc:
        logging.error("FALHA na conversão de %s.", nome_arquivo, exc_info=True)
        return (False, str(exc), None)
    finally:
        for pagina in frames_rgb:
            pagina.close()
