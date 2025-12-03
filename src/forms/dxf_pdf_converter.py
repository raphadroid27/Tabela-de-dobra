"""Conversão de DXF para PDF.

Este módulo concentra a lógica de conversão de DXF para PDF,
utilizando renderização com ezdxf (Matplotlib ou PyMuPDF).
"""

import logging
import os
from typing import Optional

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
) -> tuple[bool, str, Optional[str]]:
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
    nome_base = os.path.splitext(nome_arquivo)[0]
    nome_pdf = nome_base + ".pdf"

    path_destino = None
    if ensure_unique_path_func:
        path_destino = ensure_unique_path_func(
            os.path.join(pasta_destino, nome_pdf)
        )
    else:
        path_destino = os.path.join(pasta_destino, nome_pdf)

    try:
        doc, recovered = _load_dxf_document(path_dxf)

        if select_layout_func:
            layout_obj, layout_name = select_layout_func(doc)
        else:
            layout_obj = doc.modelspace()
            layout_name = "Model"

        if render_layout_func:
            render_layout_func(doc, layout_obj, path_destino)
        else:
            raise RuntimeError(
                "Nenhuma função de renderização foi fornecida."
            )

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
) -> tuple[any, bool]:
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
                f"Não foi possível recuperar o arquivo DXF: {exc}"
            ) from exc

        try:
            doc, auditor = EZDXF_RECOVER.readfile(path_dxf)
        except (ezdxf.DXFStructureError, ValueError) as recover_exc:
            raise DXFConversionError(
                f"Não foi possível recuperar o arquivo DXF: {recover_exc}"
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
