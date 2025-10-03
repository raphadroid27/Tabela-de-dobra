"""Infraestrutura de comparação para o formulário de arquivos.

Reúne verificação de dependências, metadados de suporte e o worker de comparação
para manter ``form_comparar_arquivos`` mais enxuto.
"""

# pylint: disable=R0914
from __future__ import annotations

import hashlib
import logging
import traceback
from typing import List, Optional, Tuple, TypedDict

from PySide6.QtCore import QObject, QThread, Signal

try:  # Bibliotecas CAD (STEP/IGES)
    from OCC.Core.BRepGProp import brepgprop  # type: ignore[attr-defined]
    from OCC.Core.GProp import GProp_GProps  # type: ignore[attr-defined]
    from OCC.Core.IGESControl import IGESControl_Reader  # type: ignore[attr-defined]
    from OCC.Core.STEPControl import STEPControl_Reader  # type: ignore[attr-defined]
    from OCC.Core.TopAbs import (  # type: ignore[attr-defined]
        TopAbs_EDGE,
        TopAbs_FACE,
        TopAbs_VERTEX,
    )
    from OCC.Core.TopExp import TopExp_Explorer  # type: ignore[attr-defined]

    PYTHON_OCC_AVAILABLE = True
except ImportError:
    brepgprop = None  # type: ignore[assignment]
    GProp_GProps = None  # type: ignore[assignment]
    IGESControl_Reader = None  # type: ignore[assignment]
    STEPControl_Reader = None  # type: ignore[assignment]
    TopAbs_EDGE = TopAbs_FACE = TopAbs_VERTEX = None  # type: ignore[assignment]
    TopExp_Explorer = None  # type: ignore[assignment]
    PYTHON_OCC_AVAILABLE = False

try:  # DXF
    import ezdxf  # type: ignore[import]
    from ezdxf import bbox as ezdxf_bbox  # type: ignore[attr-defined]
    from ezdxf.math import BoundingBox  # type: ignore[attr-defined]

    EZDXF_AVAILABLE = True
except ImportError:
    ezdxf = None  # type: ignore[assignment]
    ezdxf_bbox = None  # type: ignore[assignment]
    BoundingBox = None  # type: ignore[assignment]
    EZDXF_AVAILABLE = False

try:  # PDFs
    import fitz  # type: ignore[import]

    PYMUPDF_AVAILABLE = True
except ImportError:
    fitz = None  # type: ignore[assignment]
    PYMUPDF_AVAILABLE = False


class FileHandlerInfo(TypedDict):
    """Estrutura com metadados para cada tipo de arquivo suportado."""

    extensions: Tuple[str, ...]
    available: bool
    tooltip: str


FILE_HANDLERS: dict[str, FileHandlerInfo] = {
    "STEP": {
        "extensions": ("*.step", "*.stp"),
        "available": PYTHON_OCC_AVAILABLE,
        "tooltip": "Comparação geométrica de topologia, volume, área, etc. (Ctrl+Enter)",
    },
    "IGES": {
        "extensions": ("*.igs", "*.iges"),
        "available": PYTHON_OCC_AVAILABLE,
        "tooltip": "Comparação geométrica de topologia, volume, área, etc. (Ctrl+Enter)",
    },
    "DXF": {
        "extensions": ("*.dxf",),
        "available": EZDXF_AVAILABLE,
        "tooltip": "Comparação por contagem de entidades e extensões do desenho (Ctrl+Enter)",
    },
    "PDF": {
        "extensions": ("*.pdf",),
        "available": PYMUPDF_AVAILABLE,
        "tooltip": "Comparação por metadados, texto e imagens incorporadas (Ctrl+Enter)",
    },
    "DWG": {
        "extensions": ("*.dwg",),
        "available": True,
        "tooltip": "Comparação por hash binário (Ctrl+Enter)",
    },
}

_DEPENDENCY_MESSAGES = (
    ("python-occ-core (para STEP/IGES)", PYTHON_OCC_AVAILABLE),
    ("ezdxf (para DXF)", EZDXF_AVAILABLE),
    ("PyMuPDF (para PDF)", PYMUPDF_AVAILABLE),
)


def get_missing_dependencies() -> list[str]:
    """Retorna uma lista com as dependências opcionais ausentes."""

    return [name for name, available in _DEPENDENCY_MESSAGES if not available]


class ComparisonWorker(QThread):
    """Executa a comparação de arquivos em segundo plano."""

    progress_updated = Signal(int)
    row_compared = Signal(int, object, str, object, str, object)
    comparison_finished = Signal(bool)
    error_occurred = Signal(str)

    def __init__(
        self,
        files_a: List[str],
        files_b: List[str],
        file_type: str,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self.files_a = files_a
        self.files_b = files_b
        self.file_type = file_type
        self._is_interrupted = False

    def stop(self) -> None:
        """Sinaliza à thread que o processamento deve ser interrompido."""

        self._is_interrupted = True

    # pylint: disable=broad-except
    def run(self) -> None:  # type: ignore[override]
        """Percorre as listas e emite sinais conforme o progresso."""

        try:
            max_count = max(len(self.files_a), len(self.files_b))
            if max_count == 0:
                self.comparison_finished.emit(self._is_interrupted)
                return

            for index in range(max_count):
                if self._is_interrupted:
                    break

                path_a = self.files_a[index] if index < len(self.files_a) else None
                path_b = self.files_b[index] if index < len(self.files_b) else None

                if path_a and path_b:
                    hash_a = self._get_file_hash(path_a)
                    hash_b = self._get_file_hash(path_b)
                    if hash_a is not None and hash_a == hash_b:
                        props = ("Hash idêntico",)
                        self.row_compared.emit(index, props, "OK", props, "OK", True)
                        self.progress_updated.emit(int(((index + 1) / max_count) * 100))
                        continue

                props_a, status_a = (
                    self._get_file_properties(path_a, self.file_type)
                    if path_a
                    else (None, "Sem par")
                )
                props_b, status_b = (
                    self._get_file_properties(path_b, self.file_type)
                    if path_b
                    else (None, "Sem par")
                )
                are_equal = (props_a == props_b) if props_a and props_b else None
                self.row_compared.emit(
                    index, props_a, status_a, props_b, status_b, are_equal
                )
                self.progress_updated.emit(int(((index + 1) / max_count) * 100))
        except Exception as exc:  # pragma: no cover - salvaguarda
            logging.error("Ocorreu um erro inesperado na thread de comparação.")
            logging.error(traceback.format_exc())
            self.error_occurred.emit(f"Ocorreu um erro crítico na comparação:\n{exc}")
        finally:
            self.comparison_finished.emit(self._is_interrupted)

    def _get_file_hash(self, file_path: str) -> Optional[str]:
        """Calcula o hash SHA256 do arquivo informado."""

        sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as handle:
                for chunk in iter(lambda: handle.read(4096), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except IOError as exc:
            logging.warning(
                "Não foi possível calcular o hash para '%s': %s", file_path, exc
            )
            return None

    def _get_file_properties(
        self, file_path: str, file_type: str
    ) -> Tuple[Optional[tuple], str]:
        """Encaminha para o extrator apropriado conforme o tipo."""

        handlers: dict[str, tuple] = {}
        if PYTHON_OCC_AVAILABLE and STEPControl_Reader is not None:
            handlers["STEP"] = (self._get_cad_properties, STEPControl_Reader)
            handlers["IGES"] = (self._get_cad_properties, IGESControl_Reader)
        if EZDXF_AVAILABLE and ezdxf is not None:
            handlers["DXF"] = (self._get_dxf_properties,)
        if PYMUPDF_AVAILABLE and fitz is not None:
            handlers["PDF"] = (self._get_pdf_properties,)

        if file_type in handlers:
            extractor, *extras = handlers[file_type]
            return extractor(file_path, *extras)

        if file_type == "DWG":
            file_hash = self._get_file_hash(file_path)
            if file_hash:
                return (file_hash,), "OK"
            logging.warning("Falha ao calcular hash para arquivo DWG: %s", file_path)
            return None, "Erro ao calcular hash"

        logging.warning("Tipo de arquivo não suportado para extração: %s", file_type)
        return None, "Tipo não suportado"

    def _get_cad_properties(
        self, file_path: str, reader_class
    ) -> Tuple[Optional[tuple], str]:
        """Extrai propriedades geométricas de STEP/IGES."""

        if not PYTHON_OCC_AVAILABLE or reader_class is None or brepgprop is None:
            return None, "Biblioteca python-occ-core indisponível"

        try:
            reader = reader_class()
            if reader.ReadFile(file_path) != 1:
                logging.warning("Falha ao ler arquivo CAD: %s", file_path)
                return None, "Erro ao ler o arquivo"
            reader.TransferRoots()
            shape = reader.OneShape()
            if shape is None or shape.IsNull():
                logging.warning("Nenhuma geometria encontrada em: %s", file_path)
                return None, "Nenhuma geometria encontrada"

            num_faces = num_edges = num_vertices = 0
            explorer = TopExp_Explorer(shape, TopAbs_FACE)  # type: ignore[arg-type]
            while explorer.More():
                num_faces += 1
                explorer.Next()
            explorer.Init(shape, TopAbs_EDGE)
            while explorer.More():
                num_edges += 1
                explorer.Next()
            explorer.Init(shape, TopAbs_VERTEX)
            while explorer.More():
                num_vertices += 1
                explorer.Next()

            props_vol, props_surf = GProp_GProps(), GProp_GProps()
            brepgprop.VolumeProperties(shape, props_vol)
            brepgprop.SurfaceProperties(shape, props_surf)
            centre = props_vol.CentreOfMass()
            moments = props_vol.PrincipalProperties().Moments()

            return (
                f"{num_faces} F, {num_edges} A, {num_vertices} V",
                round(props_vol.Mass(), 6),
                round(props_surf.Mass(), 6),
                f"({centre.X():.3f}, {centre.Y():.3f}, {centre.Z():.3f})",
                f"({moments[0]:.3f}, {moments[1]:.3f}, {moments[2]:.3f})",
            ), "OK"
        except (IOError, RuntimeError, ValueError) as exc:
            logging.warning("Exceção ao processar arquivo CAD '%s': %s", file_path, exc)
            return None, f"Exceção: {exc}"

    def _get_dxf_properties(self, file_path: str) -> Tuple[Optional[tuple], str]:
        """Extrai propriedades de um DXF."""

        if not EZDXF_AVAILABLE or ezdxf is None or BoundingBox is None:
            return None, "Biblioteca ezdxf indisponível"

        try:
            doc = ezdxf.readfile(file_path)
            msp = doc.modelspace()
            bbox = None
            if ezdxf_bbox is not None:
                try:
                    bbox = ezdxf_bbox.extents(msp)
                except TypeError as exc:  # entidades sem suporte
                    logging.debug(
                        "Falha ao calcular extents via ezdxf_bbox para '%s': %s",
                        file_path,
                        exc,
                    )
            if bbox is None or not getattr(bbox, "has_data", False):
                bbox = BoundingBox()
                for entity in msp:
                    try:
                        entity_bbox = (
                            ezdxf_bbox.extents([entity]) if ezdxf_bbox else None
                        )
                    except TypeError:
                        entity_bbox = None
                    if entity_bbox and getattr(entity_bbox, "has_data", False):
                        bbox.extend(entity_bbox)

            if getattr(bbox, "has_data", False):
                extmin = (bbox.extmin.x, bbox.extmin.y)
                extmax = (bbox.extmax.x, bbox.extmax.y)
            else:
                extmin = (0.0, 0.0)
                extmax = (0.0, 0.0)
            return (
                f"{len(msp)} entidades",
                f"({extmin[0]:.3f}, {extmin[1]:.3f})",
                f"({extmax[0]:.3f}, {extmax[1]:.3f})",
            ), "OK"
        except (IOError, ezdxf.DXFStructureError, TypeError) as exc:
            logging.warning("Exceção ao processar arquivo DXF '%s': %s", file_path, exc)
            return None, f"Exceção: {exc}"

    def _get_pdf_properties(self, file_path: str) -> Tuple[Optional[tuple], str]:
        """Extrai propriedades do PDF, incluindo hashes de texto e imagens."""

        if not PYMUPDF_AVAILABLE or fitz is None:
            return None, "Biblioteca PyMuPDF ausente"

        try:
            with fitz.open(file_path) as doc:  # type: ignore[call-arg]
                metadata = getattr(doc, "metadata", {}) or {}
                text_hash = hashlib.sha256()
                image_hash = hashlib.sha256()
                image_count = 0

                for page in doc:
                    texto = page.get_text("text", sort=True)
                    if texto:
                        text_hash.update(texto.encode("utf-8"))

                    for image_info in page.get_images(full=True):
                        xref = image_info[0]
                        try:
                            extracted = doc.extract_image(xref)
                        except (ValueError, RuntimeError):
                            continue
                        image_bytes = extracted.get("image")
                        if image_bytes:
                            image_hash.update(image_bytes)
                            image_count += 1

                file_hash = self._get_file_hash(file_path) or ""
                props = (
                    doc.page_count,
                    metadata.get("author", "N/A"),
                    metadata.get("creator", "N/A"),
                    text_hash.hexdigest(),
                    image_count,
                    image_hash.hexdigest() if image_count else "",
                    file_hash,
                )
                return props, "OK"
        except (RuntimeError, ValueError, IOError) as exc:
            logging.warning("Exceção ao processar arquivo PDF '%s': %s", file_path, exc)
            return None, f"Erro: {exc}"

        return None, "Erro desconhecido"
