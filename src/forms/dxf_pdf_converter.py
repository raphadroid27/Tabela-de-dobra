"""Conversão de DXF para PDF.

Este módulo concentra a lógica de conversão de DXF para PDF,
utilizando renderização com ezdxf (Matplotlib ou PyMuPDF).
"""

import logging
import os
from typing import Any, Optional

from src.forms.common.converters_common import get_file_destination

# Importações opcionais de ezdxf
try:
    import ezdxf
    from ezdxf import recover as ezdxf_recover

    EZDXF_AVAILABLE = True
    EZDXF_RECOVER = ezdxf_recover
except ImportError:
    ezdxf = None
    EZDXF_AVAILABLE = False
    EZDXF_RECOVER = None


class DXFConversionError(RuntimeError):
    """Erro controlado para problemas de leitura de arquivos DXF."""


def converter_dxf_para_pdf(
    path_dxf: str,
    pasta_destino: str,
    select_layout_func=None,
    render_layout_func=None,
    ensure_unique_path_func=None,
    nome_base_override: Optional[str] = None,
) -> tuple[bool, str, Optional[str]]:
    # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
    """Converte um arquivo DXF para PDF.

    Args:
        path_dxf: Caminho do arquivo DXF
        pasta_destino: Pasta onde salvar o resultado
        select_layout_func: Função para selecionar layout
        render_layout_func: Função para renderizar layout
        ensure_unique_path_func: Função para garantir caminhos únicos

    Returns:
        Tuple (sucesso, mensagem, caminho_arquivo_resultado)
    """
    if not EZDXF_AVAILABLE or ezdxf is None:
        return (
            False,
            "Biblioteca 'ezdxf' indisponível para renderização.",
            None,
        )

    nome_arquivo = os.path.basename(path_dxf)
    nome_base = nome_base_override or os.path.splitext(nome_arquivo)[0]
    nome_pdf = nome_base + ".pdf"

    try:
        path_destino = get_file_destination(
            pasta_destino,
            nome_pdf,
            ensure_unique_path_func,
        )
        doc, recovered = _load_dxf_document(path_dxf)

        if select_layout_func:
            layout_obj, layout_name = select_layout_func(doc)
        else:
            layout_obj = doc.modelspace()
            layout_name = "Model"

        if render_layout_func:
            render_layout_func(doc, layout_obj, path_destino)
        else:
            raise RuntimeError("Nenhuma função de renderização foi fornecida.")

        mensagem = (
            "Conversão bem-sucedida"
            if layout_name == "Model"
            else f"Conversão bem-sucedida (layout: {layout_name})"
        )
        if recovered:
            mensagem += " — DXF recuperado"

        return (True, mensagem, path_destino)

    except DXFConversionError as exc:
        logging.warning(
            "Conversão cancelada para %s: %s",
            nome_arquivo,
            exc,
        )
        return (False, str(exc), None)
    except (ezdxf.DXFStructureError, IOError, OSError, RuntimeError) as exc:
        logging.error(
            "FALHA na conversão de %s.",
            nome_arquivo,
            exc_info=True,
        )
        return (False, str(exc), None)


def _load_dxf_document(
    path_dxf: str,
) -> tuple[Any, bool]:
    """Carrega um documento DXF com recuperação de erros.

    Args:
        path_dxf: Caminho do arquivo DXF

    Returns:
        Tuple (documento, foi_recuperado)
    """
    if not EZDXF_AVAILABLE or ezdxf is None:
        raise RuntimeError("Biblioteca 'ezdxf' indisponível para renderização.")

    try:
        return ezdxf.readfile(path_dxf), False
    except (ezdxf.DXFStructureError, ValueError) as exc:
        logging.warning(
            "Falha na leitura direta do DXF '%s': %s. Tentando recover...",
            path_dxf,
            exc,
        )

        if EZDXF_RECOVER is None:
            raise DXFConversionError(
                _format_dxf_error_message(path_dxf, exc)
            ) from exc

        try:
            doc, auditor = EZDXF_RECOVER.readfile(path_dxf)
        except (ezdxf.DXFStructureError, ValueError) as recover_exc:
            raise DXFConversionError(
                _format_dxf_error_message(path_dxf, recover_exc)
            ) from recover_exc

        if auditor is not None:
            errors = list(getattr(auditor, "errors", []) or [])
            if getattr(auditor, "has_errors", bool(errors)) and errors:
                preview = "; ".join(str(err) for err in errors[:3])
                logging.warning(
                    "DXF '%s' recuperado com %d erro(s). Exemplos: %s",
                    path_dxf,
                    len(errors),
                    preview,
                )

        return doc, True


def _format_dxf_error_message(path_dxf: str, error: Exception) -> str:
    message = str(error)
    normalized = message.lower()
    if "invalid handle 0" in normalized:
        return (
            "DXF corrompido: identificador '0' inválido.\n"
            "Reexporte o arquivo a partir da origem (ex.: salvar como DXF R12)\n"
            "ou utilize a função de auditoria do CAD."
        )
    return f"Falha ao recuperar DXF '{os.path.basename(path_dxf)}': {message}"
