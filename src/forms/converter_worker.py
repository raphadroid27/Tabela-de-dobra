"""Infraestrutura de suporte para conversão de arquivos.

Este módulo concentra a lógica pesada usada por ``form_converter_arquivos``
para reduzir o tamanho do formulário principal e facilitar a reutilização.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess  # nosec B404 - necessário para integração com conversores externos
import tempfile
import traceback
from pathlib import Path
from typing import Any, Callable, List, Optional, Tuple

from PySide6.QtCore import QThread, Signal

from src.forms.common.converters_common import run_oda_command
from src.forms.dwg_converter import converter_dwg_para_dwg_2013
from src.forms.dwg_pdf_converter import converter_dwg_para_pdf
from src.forms.dxf_pdf_converter import converter_dxf_para_pdf
from src.forms.pdf_dxf_converter import converter_pdf_para_dxf
from src.forms.tif_converter import converter_tif_para_pdf


try:  # Pillow
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Valores padrão para módulos opcionais
# pylint: disable=invalid-name
Frontend = RenderContext = None  # type: ignore[assignment]
BackgroundPolicy = ColorPolicy = None  # type: ignore[assignment]
BoundingBox = None  # type: ignore[assignment]
BoundingBox2d = Margins = Page = Settings = Units = None  # type: ignore[assignment]
MatplotlibBackend = None  # type: ignore[assignment]
PyMuPdfBackend = None  # type: ignore[assignment]
plt = None  # type: ignore[assignment]
# pylint: enable=invalid-name

EZDXF_RECOVER = None  # type: ignore[assignment]
try:  # ezdxf e estruturas de desenho
    import ezdxf  # type: ignore[import]

    EZDXF_AVAILABLE = True
    try:
        from ezdxf.addons.drawing import Frontend, RenderContext
        from ezdxf.addons.drawing.config import BackgroundPolicy, ColorPolicy
        from ezdxf.addons.drawing.layout import (
            BoundingBox2d,
            Margins,
            Page,
            Settings,
            Units,
        )
        from ezdxf.math import BoundingBox
    except ImportError:
        Frontend = RenderContext = None  # type: ignore[assignment]
        BackgroundPolicy = ColorPolicy = None  # type: ignore[assignment]
        BoundingBox = None  # type: ignore[assignment]
        # type: ignore[assignment]
        BoundingBox2d = Margins = Page = Settings = Units = None
        EZDXF_AVAILABLE = False

    if EZDXF_AVAILABLE:
        try:
            from ezdxf.addons.drawing.matplotlib import (  # type: ignore[import]
                MatplotlibBackend,
            )
        except ImportError:
            MatplotlibBackend = None  # type: ignore[assignment]

        try:
            from ezdxf.addons.drawing.pymupdf import (  # type: ignore[import]
                PyMuPdfBackend,
            )
        except ImportError:
            PyMuPdfBackend = None  # type: ignore[assignment]

        try:
            from ezdxf import recover as ezdxf_recover  # type: ignore[import]
        except ImportError:
            EZDXF_RECOVER = None  # type: ignore[assignment]
        else:
            EZDXF_RECOVER = ezdxf_recover

except ImportError:
    ezdxf = None  # type: ignore[assignment]
    EZDXF_AVAILABLE = False

if MatplotlibBackend is not None:
    try:  # Matplotlib backend
        import matplotlib.pyplot as plt  # type: ignore[import]
    except ImportError:
        plt = None  # type: ignore[assignment]

try:  # PyMuPDF para análise de PDF
    import fitz  # type: ignore[import]

    FITZ_AVAILABLE = True
except ImportError:
    fitz = None  # type: ignore[assignment]
    FITZ_AVAILABLE = False

MATPLOTLIB_BACKEND_AVAILABLE = bool(MatplotlibBackend and plt)
PYMUPDF_BACKEND_AVAILABLE = bool(PyMuPdfBackend)
CAD_RENDER_AVAILABLE = EZDXF_AVAILABLE and (
    MATPLOTLIB_BACKEND_AVAILABLE or PYMUPDF_BACKEND_AVAILABLE
)


def _collect_render_config() -> dict[str, object]:
    config_changes: dict[str, object] = {}
    if BackgroundPolicy:
        config_changes["background_policy"] = BackgroundPolicy.WHITE
        config_changes["custom_bg_color"] = "#FFFFFF"
    if ColorPolicy:
        config_changes["color_policy"] = ColorPolicy.BLACK
    return config_changes


def _update_render_config(target: Any) -> None:
    config_changes = _collect_render_config()
    if config_changes and hasattr(target, "config"):
        target.config = target.config.with_changes(**config_changes)


def _log_subprocess_output(
    result: Any, context: str, *, stderr_level: int = logging.DEBUG
) -> None:
    stdout = getattr(result, "stdout", "")
    if stdout:
        logging.debug("%s stdout:\n%s", context, str(stdout).strip())

    stderr = getattr(result, "stderr", "")
    if stderr:
        logging.log(stderr_level, "%s stderr:\n%s", context, str(stderr).strip())


def find_external_program(
    program_name: str, executable_name: str, common_paths: List[str]
) -> Optional[str]:
    """Tenta localizar um executável externo no sistema."""
    path = shutil.which(executable_name)
    if path and os.path.isfile(path):
        return path

    for common_path in common_paths:
        if "*" in common_path:
            match = _search_globbed_program(common_path, executable_name)
            if match:
                return match
            continue

        full_path = os.path.join(common_path, executable_name)
        if os.path.isfile(full_path):
            return full_path

    logging.warning("'%s' não foi encontrado no sistema.", program_name)
    return None


def _search_globbed_program(path_pattern: str, executable_name: str) -> Optional[str]:
    """Procura o executável seguindo um padrão com curingas."""

    base_dir = os.path.dirname(path_pattern)
    if not os.path.isdir(base_dir):
        return None

    prefix = os.path.basename(path_pattern).replace("*", "")
    for item in os.listdir(base_dir):
        if not item.startswith(prefix):
            continue
        dir_path = os.path.join(base_dir, item)
        if not os.path.isdir(dir_path):
            continue
        candidate = os.path.join(dir_path, executable_name)
        if os.path.isfile(candidate):
            return candidate

    return None


INKSCAPE_EXECUTABLE = find_external_program(
    "Inkscape", "inkscape.exe", ["C:/Program Files/Inkscape/bin"]
)
ODA_CONVERTER_EXECUTABLE = find_external_program(
    "ODA File Converter",
    "ODAFileConverter.exe",
    ["C:/Program Files/ODA/ODAFileConverter*"],
)

INKSCAPE_AVAILABLE = bool(INKSCAPE_EXECUTABLE)
ODA_CONVERTER_AVAILABLE = bool(ODA_CONVERTER_EXECUTABLE)


CONVERSION_HANDLERS = {
    "DWG para PDF": {
        "extensions": ("*.dwg",),
        "tooltip": "Converte DWG para PDF (Ctrl+Enter)",
        "enabled": ODA_CONVERTER_AVAILABLE and CAD_RENDER_AVAILABLE,
        "dependency_msg": (
            "O ODA Converter e bibliotecas ezdxf com um backend de renderização"
            " (Matplotlib ou PyMuPDF) são necessários."
        ),
    },
    "DWG para DWG 2013": {
        "extensions": ("*.dwg",),
        "tooltip": "Converte DWG para DWG versão 2013 (Ctrl+Enter)",
        "enabled": ODA_CONVERTER_AVAILABLE,
        "dependency_msg": "O ODA Converter é necessário.",
    },
    "TIF para PDF": {
        "extensions": ("*.tif", "*.tiff"),
        "tooltip": "Converte TIF para PDF (Ctrl+Enter)",
        "enabled": PIL_AVAILABLE,
        "dependency_msg": "A biblioteca 'Pillow' é necessária.",
    },
    "DXF para PDF": {
        "extensions": ("*.dxf",),
        "tooltip": "Converte DXF para PDF (Ctrl+Enter)",
        "enabled": CAD_RENDER_AVAILABLE,
        "dependency_msg": (
            "É necessário ter 'ezdxf' e um backend de renderização"
            " (Matplotlib ou PyMuPDF)."
        ),
    },
    "PDF para DXF": {
        "extensions": ("*.pdf",),
        "tooltip": "Converte PDF para DXF (Ctrl+Enter)",
        "enabled": INKSCAPE_AVAILABLE,
        "dependency_msg": "O software Inkscape (instalado e/ou no PATH) é necessário.",
    },
}


class ConversionWorker(QThread):
    """Executa a conversão em segundo plano."""

    progress_percent = Signal(int)
    file_processed = Signal(int, object, bool, str)
    processo_finalizado = Signal(bool)
    error_occurred = Signal(str)

    def __init__(
        self,
        conversion_config: dict,
        parent=None,
    ) -> None:
        """Inicializa ConversionWorker com configuração centralizada.

        Args:
            conversion_config: Dict com {pasta_destino, files, conversion_type, substituir_original}
            parent: Widget pai (QObject)
        """
        super().__init__(parent)
        self.pasta_destino = conversion_config["pasta_destino"]
        self.files = conversion_config["files"]
        self.conversion_type = conversion_config["conversion_type"]
        self.substituir_original = conversion_config.get("substituir_original", False)
        self._is_interrupted = False
        self._conversion_handlers = self._build_conversion_handlers()

    def stop(self) -> None:
        """Sinaliza à thread para interromper a execução."""
        self._is_interrupted = True

    @staticmethod
    def _ensure_unique_path(path_destino: str) -> str:
        """Evita sobrescrever arquivos existentes criando sufixos incrementais."""

        candidate = Path(path_destino)
        if not candidate.exists():
            return str(candidate)

        stem = candidate.stem
        suffix = candidate.suffix
        parent = candidate.parent
        counter = 1
        while True:
            new_candidate = parent / f"{stem}_{counter}{suffix}"
            if not new_candidate.exists():
                return str(new_candidate)
            counter += 1

    # pylint: disable=too-many-branches,too-many-locals
    def run(self) -> None:  # type: ignore[override]
        """Ponto de entrada da thread de conversão."""
        try:
            total = len(self.files)
            for idx, (row, path_origem) in enumerate(self.files, start=1):
                if self._is_interrupted:
                    break

                handler = self._conversion_handlers.get(self.conversion_type)
                if handler is None:
                    logging.error(
                        "Tipo de conversão desconhecido: %s", self.conversion_type
                    )
                    continue

                handler(row, path_origem)

                percent = int((idx / total) * 100)
                self.progress_percent.emit(percent)
        except (
            OSError,
            subprocess.CalledProcessError,
            subprocess.TimeoutExpired,
            FileNotFoundError,
        ) as exc:
            logging.error("Ocorreu um erro na thread de conversão.")
            logging.error(traceback.format_exc())
            self.error_occurred.emit(f"Ocorreu um erro crítico na conversão:\n{exc}")
        finally:
            self.processo_finalizado.emit(self._is_interrupted)

    def _build_conversion_handlers(self) -> dict[str, Callable[[int, str], None]]:
        return {
            "TIF para PDF": self._convert_tif_to_pdf,
            "DWG para PDF": self._convert_dwg_to_pdf,
            "DWG para DWG 2013": self._convert_dwg_to_dwg_2013,
            "PDF para DXF": self._convert_pdf_to_dxf,
            "DXF para PDF": self._convert_dxf_to_pdf_handler,
        }

    def _convert_dxf_to_pdf_handler(self, row: int, path_origem: str) -> None:
        self._convert_dxf_to_pdf(row, path_origem, path_origem)

    def _convert_dwg_to_pdf(self, row: int, path_origem: str) -> None:
        """Converte DWG para PDF delegando ao helper especializado."""
        sucesso, mensagem, path_resultado = converter_dwg_para_pdf(
            path_origem=path_origem,
            generate_dxf_func=self._generate_intermediate_dxf,
            convert_dxf_to_pdf_func=self._convert_dxf_temp_to_pdf,
        )

        if self._is_interrupted:
            return

        self.file_processed.emit(row, path_resultado or "", sucesso, mensagem)

    def _convert_dwg_to_dwg_2013(self, row: int, path_origem: str) -> None:
        """Converte DWG para DWG versão 2013 utilizando o ODA Converter."""
        sucesso, mensagem, arquivos = converter_dwg_para_dwg_2013(
            path_origem=path_origem,
            pasta_destino=self.pasta_destino,
            oda_executable=ODA_CONVERTER_EXECUTABLE,
            substituir_original=self.substituir_original,
            ensure_unique_path_func=self._ensure_unique_path,
        )

        if sucesso:
            path_resultado = arquivos[0] if arquivos else ""
            self.file_processed.emit(row, path_resultado, True, mensagem)
        else:
            path_resultado = arquivos[0] if arquivos else ""
            self.file_processed.emit(row, path_resultado, sucesso, mensagem)

    def _generate_intermediate_dxf(
        self, path_origem: str, nome_arquivo: str, path_dxf_temp: str
    ) -> tuple[bool, str]:
        """Executa o ODA Converter para gerar um DXF temporário."""

        if not ODA_CONVERTER_EXECUTABLE:
            return (False, "ODA Converter não está configurado corretamente.")

        with tempfile.TemporaryDirectory() as temp_dir:
            command = [
                ODA_CONVERTER_EXECUTABLE,
                os.path.dirname(path_origem),
                temp_dir,
                "ACAD2018",
                "DXF",
                "0",
                "1",
                nome_arquivo,
            ]

            result = run_oda_command(command, "ODA Converter DWG->DXF")

            _log_subprocess_output(result, "ODA Converter", stderr_level=logging.DEBUG)

            nome_base = Path(nome_arquivo).stem
            expected_dxf = Path(temp_dir, f"{nome_base}.dxf")
            if expected_dxf.exists():
                shutil.move(str(expected_dxf), path_dxf_temp)
                return (True, "DXF intermediário gerado")

            fallback = next(Path(temp_dir).glob("*.dxf"), None)
            if fallback:
                shutil.move(str(fallback), path_dxf_temp)
                return (True, "DXF intermediário gerado")

            logging.error("FALHA: Arquivo DXF intermediário não foi criado.")
            return (False, "Arquivo DXF intermediário não foi criado.")

    def _convert_dxf_temp_to_pdf(
        self, path_dxf: str, path_original_para_nome: str
    ) -> tuple[bool, str, Optional[str]]:
        """Encaminha conversão DXF->PDF para o helper compartilhado."""

        nome_destino_base = os.path.splitext(
            os.path.basename(path_original_para_nome)
        )[0]
        return converter_dxf_para_pdf(
            path_dxf=path_dxf,
            pasta_destino=self.pasta_destino,
            select_layout_func=self._select_layout_for_render,
            render_layout_func=self._render_layout_to_pdf,
            ensure_unique_path_func=self._ensure_unique_path,
            nome_base_override=nome_destino_base,
        )

    def _convert_tif_to_pdf(self, row: int, path_origem: str) -> None:
        """Converte um único arquivo TIF para PDF."""
        sucesso, mensagem, path_destino = converter_tif_para_pdf(
            path_origem=path_origem,
            pasta_destino=self.pasta_destino,
            ensure_unique_path_func=self._ensure_unique_path,
        )
        self.file_processed.emit(row, path_destino or "", sucesso, mensagem)

    def _convert_dxf_to_pdf(
        self, row: int, path_dxf: str, path_original_para_nome: str
    ) -> None:
        """Converte um arquivo DXF para PDF via helper especializado."""
        sucesso, mensagem, path_destino = self._convert_dxf_temp_to_pdf(
            path_dxf,
            path_original_para_nome,
        )
        self.file_processed.emit(row, path_destino or "", sucesso, mensagem)

    def _select_layout_for_render(self, doc):
        model = doc.modelspace()
        if self._layout_entity_count(model) > 0:
            return model, "Model"

        for layout_obj in doc.layouts:  # type: ignore[not-an-iterable]
            if getattr(layout_obj, "name", "Model") == "Model":
                continue
            if self._layout_entity_count(layout_obj) > 0:
                return layout_obj, getattr(layout_obj, "name", "Layout")

        return model, "Model"

    @staticmethod
    def _layout_entity_count(layout_obj) -> int:
        try:
            return len(layout_obj)
        except TypeError:
            try:
                iterator = iter(layout_obj)  # type: ignore[arg-type]
            except TypeError:
                return 0
            return 1 if next(iterator, None) is not None else 0

    def _render_layout_to_pdf(self, doc, layout_obj, path_destino: str) -> None:
        if PYMUPDF_BACKEND_AVAILABLE:
            self._render_with_pymupdf(doc, layout_obj, path_destino)
            return
        if MATPLOTLIB_BACKEND_AVAILABLE:
            self._render_with_matplotlib(doc, layout_obj, path_destino)
            return
        raise RuntimeError("Nenhum backend de renderização DXF está disponível.")

    def _render_with_pymupdf(self, doc, layout_obj, path_destino: str) -> None:
        if not (
            PYMUPDF_BACKEND_AVAILABLE
            and PyMuPdfBackend
            and Page
            and Settings
            and Margins
            and Units
        ):
            raise RuntimeError("Backend PyMuPDF indisponível para renderização de DXF.")

        backend = PyMuPdfBackend()
        try:
            backend.set_background("#FFFFFF")
        except AttributeError:
            logging.debug(
                "Backend PyMuPDF sem suporte a set_background; usando padrão."
            )
        ctx = RenderContext(doc)
        frontend = Frontend(ctx, backend)
        self._apply_monochrome_override(frontend)
        _update_render_config(frontend)
        frontend.draw_layout(layout_obj, finalize=True)
        backend.finalize()

        bbox = self._layout_bounding_box(layout_obj)
        render_box = None
        width_mm, height_mm = self._preferred_page_size_mm(bbox)
        if bbox and BoundingBox2d:
            render_box = BoundingBox2d(
                [
                    (bbox.extmin.x, bbox.extmin.y),
                    (bbox.extmax.x, bbox.extmax.y),
                ]
            )

        page = Page(
            width_mm,
            height_mm,
            units=Units.mm,
            margins=Margins(5, 5, 5, 5),
        )
        pdf_bytes = backend.get_pdf_bytes(
            page,
            settings=Settings(fit_page=True, output_layers=True),
            render_box=render_box,
        )
        with open(path_destino, "wb") as destino:
            destino.write(pdf_bytes)

    def _render_with_matplotlib(self, doc, layout_obj, path_destino: str) -> None:
        if not (MATPLOTLIB_BACKEND_AVAILABLE and plt and MatplotlibBackend):
            raise RuntimeError(
                "Backend Matplotlib indisponível para renderização de DXF."
            )

        bbox = self._layout_bounding_box(layout_obj)
        width_mm, height_mm = self._preferred_page_size_mm(bbox)
        if width_mm == 0 or height_mm == 0:
            width_mm, height_mm = 420.0, 297.0

        fig = plt.figure(figsize=(width_mm / 25.4, height_mm / 25.4), dpi=300)
        fig.patch.set_facecolor("white")
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_axis_off()
        ax.set_facecolor("white")

        ctx = RenderContext(doc)
        backend = MatplotlibBackend(ax)
        _update_render_config(backend)
        frontend = Frontend(ctx, backend)
        self._apply_monochrome_override(frontend)
        frontend.draw_layout(layout_obj, finalize=True)

        fig.savefig(
            path_destino,
            dpi=300,
            format="pdf",
            bbox_inches="tight",
            pad_inches=0,
        )
        plt.close(fig)

    @staticmethod
    def _apply_monochrome_override(frontend) -> None:
        """Força todas as entidades a serem renderizadas em preto."""

        if not hasattr(frontend, "push_property_override_function"):
            return

        def _force_black(_entity, properties) -> None:
            if properties is None:
                return

            color = getattr(properties, "color", "#000000")
            alpha_suffix = ""
            if isinstance(color, str) and len(color) == 9:
                alpha_suffix = color[-2:]
            properties.color = "#000000" + alpha_suffix

            if hasattr(properties, "pen"):
                properties.pen = 7

            filling = getattr(properties, "filling", None)
            if filling is not None:
                if hasattr(filling, "gradient_color1"):
                    filling.gradient_color1 = "#000000"
                if hasattr(filling, "gradient_color2"):
                    filling.gradient_color2 = "#000000"

        frontend.push_property_override_function(_force_black)

    def _split_pdf_if_needed(self, pdf_path: str) -> Tuple[List[str], int]:
        """Divide PDFs multipágina em arquivos individuais quando possível."""

        if not (FITZ_AVAILABLE and fitz):
            logging.info(
                "PyMuPDF indisponível, conversão multi-página dependerá do Inkscape."
            )
            return [pdf_path], 1

        try:
            with fitz.open(pdf_path) as doc:  # type: ignore[call-arg]
                total_pages = doc.page_count
                if total_pages <= 1:
                    return [pdf_path], total_pages

                page_paths: List[str] = []
                base_dir = os.path.dirname(pdf_path)
                for idx in range(total_pages):
                    single_doc = fitz.open()  # type: ignore[call-arg]
                    single_doc.insert_pdf(doc, from_page=idx, to_page=idx)
                    page_path = self._ensure_unique_path(
                        os.path.join(base_dir, f"pagina_{idx + 1}.pdf")
                    )
                    single_doc.save(page_path)
                    single_doc.close()
                    page_paths.append(page_path)
                logging.debug(
                    "PDF '%s' dividido em %d páginas temporárias.",
                    os.path.basename(pdf_path),
                    total_pages,
                )
                return page_paths, total_pages
        except (RuntimeError, ValueError, IOError) as exc:
            logging.warning("Falha ao segmentar PDF multipágina: %s", exc)
        return [pdf_path], 1

    def _layout_bounding_box(self, layout_obj):
        if not BoundingBox:
            return None
        try:
            bbox = BoundingBox(layout_obj)
        except (ValueError, ezdxf.DXFStructureError, TypeError):
            return None
        return bbox if getattr(bbox, "has_data", False) else None

    def _preferred_page_size_mm(self, bbox) -> tuple[float, float]:
        if not bbox:
            return 420.0, 297.0
        width, height = self._extract_bbox_dimensions(bbox)
        width = self._clamp_page_size(width or 420.0)
        height = self._clamp_page_size(height or 297.0)
        return width, height

    @staticmethod
    def _extract_bbox_dimensions(bbox) -> tuple[float, float]:
        width = height = 0.0
        try:
            size = bbox.size
            width = float(getattr(size, "x", size[0]))
            height = float(getattr(size, "y", size[1]))
        except (AttributeError, IndexError, TypeError):
            try:
                width = float(bbox.extmax.x - bbox.extmin.x)
                height = float(bbox.extmax.y - bbox.extmin.y)
            except AttributeError:
                pass
        return abs(width), abs(height)

    @staticmethod
    def _clamp_page_size(value: float) -> float:
        return max(50.0, min(value, 2000.0))

    def _prepare_pdf_page_sources(
        self, temp_pdf_path: str, original_name: str
    ) -> Tuple[List[str], int, bool]:
        page_sources, total_pages = self._split_pdf_if_needed(temp_pdf_path)
        use_page_numbers = False

        if total_pages > len(page_sources):
            logging.info(
                "PDF '%s' possui %d página(s), mas apenas %d fonte(s) foram geradas; "
                "usando o arquivo original com parâmetros de página.",
                original_name,
                total_pages,
                len(page_sources),
            )
            if page_sources:
                page_sources = [page_sources[0]] * total_pages
                use_page_numbers = True
        else:
            total_pages = len(page_sources)

        return page_sources, total_pages, use_page_numbers

    def _convert_pdf_to_dxf(self, row: int, path_origem: str) -> None:
        sucesso, mensagem, arquivos_gerados = converter_pdf_para_dxf(
            path_origem=path_origem,
            pasta_destino=self.pasta_destino,
            inkscape_executable=INKSCAPE_EXECUTABLE,
            prepare_pdf_pages_func=self._prepare_pdf_page_sources,
            ensure_unique_path_func=self._ensure_unique_path,
        )

        resultado = arquivos_gerados if arquivos_gerados else ""
        self.file_processed.emit(row, resultado, sucesso, mensagem)
