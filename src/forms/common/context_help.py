"""Conteúdo centralizado de ajuda contextual para os formulários."""

from __future__ import annotations

from typing import Callable, Dict, Iterable, Iterator, List, Optional, Tuple

from PySide6.QtWidgets import QWidget

from src.utils.utilitarios import obter_dir_help_content, show_info

# pylint: disable=C0301

HelpEntry = Tuple[str, str]
ManualLauncher = Callable[[Optional[QWidget], Optional[str], bool], object]

_manual_launcher: ManualLauncher | None = None

_DEFAULT_ENTRY: HelpEntry = (
    "Ajuda indisponível",
    "Ainda não há instruções contextuais para esta janela.",
)

_HELP_CONTENT: Dict[str, HelpEntry] = {}

# Diretório onde os arquivos HTML externos residem (script ou executável)
_HELP_DIR = obter_dir_help_content()

_SECTION_FILE_MAP = {
    "main": "main.html",
    "impressao": "impressao.html",
    "comparar": "comparar.html",
    "converter": "converter.html",
    "cadastro": "cadastro.html",
    "cadastro_adicao": "cadastro_adicao.html",
    "cadastro_edicao": "cadastro_edicao.html",
    "razao_rie": "razao_rie.html",
    "spring_back": "spring_back.html",
    "autenticacao": "autenticacao.html",
    "manual": "manual.html",
    "sobre": "sobre.html",
    "admin": "admin.html",
}


def _load_help_contents() -> None:
    """Carrega o conteúdo HTML dos arquivos externos para o dicionário interno.

    Caso um arquivo não exista, a chave é ignorada (ou poderia receber fallback).
    O título (primeiro elemento do HelpEntry) é derivado da primeira tag <h4> encontrada
    ou, se ausente, do nome da chave capitalizado.
    """
    if _HELP_CONTENT:  # já carregado
        return
    for key, filename in _SECTION_FILE_MAP.items():
        path = _HELP_DIR / filename
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        # Extrair título rudimentar
        title = _extract_title(text) or f"<h4>{key.title()}</h4>"
        body = text
        if title:
            # Remover primeira ocorrência do título no início (ignorando espaços iniciais)
            stripped = body.lstrip()
            if stripped.startswith(title):
                body = stripped[len(title):].lstrip()
        _HELP_CONTENT[key] = (title, body)


def _extract_title(html: str) -> Optional[str]:
    start = html.find("<h4")
    if start == -1:
        return None
    end = html.find("</h4>", start)
    if end == -1:
        return None
    end += len("</h4>")
    return html[start:end]


def register_manual_launcher(launcher: ManualLauncher) -> None:
    """Registra o callback responsável por abrir o manual completo."""

    global _manual_launcher  # pylint: disable=global-statement
    _manual_launcher = launcher


def show_help(key: str, parent: QWidget | None = None) -> None:
    """Exibe o conteúdo de ajuda associado à chave fornecida."""
    _load_help_contents()

    try:
        if _manual_launcher is not None:
            _manual_launcher(parent, key, True)
            return
    except RuntimeError:  # pragma: no cover - fallback
        pass

    title, message = _HELP_CONTENT.get(key, _DEFAULT_ENTRY)
    show_info(title, message, parent=parent)


def get_help_entry(key: str) -> HelpEntry:
    """Retorna a entrada de ajuda correspondente à chave ou o fallback padrão."""
    _load_help_contents()
    return _HELP_CONTENT.get(key, _DEFAULT_ENTRY)


def iter_help_entries(
    keys: Iterable[str] | None = None,
    *,
    include_missing: bool = True,
) -> Iterator[Tuple[str, HelpEntry]]:
    """Itera sobre entradas de ajuda.

    Args:
        keys: ordem opcional de chaves desejadas.
        include_missing: se True, chaves desconhecidas rendem fallback padrão.
    """

    _load_help_contents()
    if keys is not None:
        seen: List[str] = []
        for key in keys:
            if key in seen:
                continue
            entry = _HELP_CONTENT.get(key)
            if entry is None:
                if include_missing:
                    seen.append(key)
                    yield key, _DEFAULT_ENTRY
                continue
            seen.append(key)
            yield key, entry

        for key, entry in _HELP_CONTENT.items():
            if key not in seen:
                yield key, entry
        return

    yield from _HELP_CONTENT.items()
