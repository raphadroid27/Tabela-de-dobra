"""Funções e constantes utilitárias genéricas para a aplicação.

Este módulo centraliza a gestão de caminhos, a configuração de logs e as
funções de diálogo com o usuário (QMessageBox, QInputDialog).
"""

import ast
import logging
import logging.handlers
import operator as op
import os
import re
import shutil
import subprocess  # nosec B404 - integração controlada com ferramentas externas
import sys
import unicodedata  # Importado para normalização de texto
from pathlib import Path
from typing import Optional, Sequence, Union

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QInputDialog, QLayout, QLineEdit, QMessageBox, QWidget

from src.config import globals as g
from src.utils.janelas import Janela

FILE_OPEN_EXCEPTIONS = (
    OSError,
    subprocess.SubprocessError,
    RuntimeError,
)


LOGGER = logging.getLogger(__name__)

_OPS = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv}


# --- 1. LÓGICA CENTRALIZADA DE CAMINHOS ---


def obter_dir_base() -> str:
    """Retorna o diretório base da aplicação de forma consistente.

    Verifica se a aplicação está rodando como um script ou como um executável
    "congelado" para determinar o caminho raiz correto.

    Returns:
        str: O caminho absoluto para o diretório raiz da aplicação.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    # Em modo de script, assume-se que este arquivo está em 'src/utils',
    # então o diretório base está dois níveis acima.
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def obter_caminho_asset(path_relativo: str) -> str:
    """Retorna o caminho absoluto de um asset (arquivo estático).

    Compatível com executáveis gerados pelo PyInstaller (OneFile ou OneDir).

    Args:
        path_relativo (str): Caminho relativo do arquivo (ex: 'assets/imagem.png').

    Returns:
        str: Caminho absoluto para o recurso.
    """
    if getattr(sys, "frozen", False):
        # No PyInstaller (onefile), os arquivos são extraídos em _MEIPASS
        base_path = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base_path = obter_dir_base()

    return os.path.join(base_path, path_relativo)


def obter_dir_icone():
    """
    Retorna o caminho correto para o arquivo de ícone,
    considerando o modo de execução (normal ou empacotado).
    """
    if getattr(sys, "frozen", False):  # Verifica se está empacotado
        base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    else:
        base_path = os.path.abspath(".")  # Diretório atual no modo normal

    return os.path.join(base_path, "assets", "icone.ico")


def obter_caminho_svg(nome_arquivo: str) -> str:
    """
    Retorna o caminho correto para arquivos SVG,
    considerando o modo de execução (normal ou empacotado).

    Args:
        nome_arquivo: Nome do arquivo SVG (ex: 'arrow_down.svg')

    Returns:
        str: Caminho absoluto para o arquivo SVG
    """
    if getattr(sys, "frozen", False):  # Verifica se está empacotado
        base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    else:
        base_path = os.path.abspath(".")  # Diretório atual no modo normal

    return os.path.join(base_path, "assets", nome_arquivo)


def obter_dir_help_content() -> Path:
    """Retorna o diretório onde os HTMLs de ajuda estão armazenados."""
    candidates = []

    meipass_dir = getattr(sys, "_MEIPASS", None)
    if meipass_dir:
        candidates.append(Path(meipass_dir) / "forms" / "common" / "help_content")

    candidates.extend(
        [
            Path(BASE_DIR) / "forms" / "common" / "help_content",
            Path(BASE_DIR) / "src" / "forms" / "common" / "help_content",
            Path(__file__).resolve().parents[2] / "forms" / "common" / "help_content",
        ]
    )

    for candidate in candidates:
        if candidate.is_dir():
            return candidate

    return candidates[0]


# --- Constantes de Caminhos Globais ---


BASE_DIR = obter_dir_base()

# Diretório de banco de dados
DATABASE_DIR = os.path.join(BASE_DIR, "database")
DB_PATH = os.path.join(DATABASE_DIR, "tabela_de_dobra.db")

# Ícone da aplicação
ICON_PATH = obter_dir_icone()

# Diretório de logs
LOG_DIR = os.path.join(BASE_DIR, "logs")

# Configuração de AppData para dados do usuário
APPDATA_DIR = os.environ.get(
    "APPDATA", os.path.join(os.environ["USERPROFILE"], "AppData", "Roaming")
)

# Diretórios para comunicação entre processos (IPC) - mantidos no diretório base
RUNTIME_DIR = os.path.join(BASE_DIR, ".runtime", "calculadora_dobra")
SESSION_DIR = os.path.join(RUNTIME_DIR, "sessions")
COMMAND_DIR = os.path.join(RUNTIME_DIR, "commands")

# Cache movido para AppData
CACHE_DIR = os.path.join(APPDATA_DIR, "Calculadora de Dobra", "cache")


# Margens e espaçamentos padrão para layouts
MARGEM_PADRAO = 5
ESPACAMENTO_PADRAO = 5

# Nome padronizado para marcar widgets que não devem ser alterados pelo monitor
SYSTEM_WIDGET_ATTR = "_is_system_widget"

# === CONSTANTES DE WIDGETS ===

# Lista de widgets do cabeçalho principal
WIDGET_CABECALHO = [
    "MAT_COMB",
    "ESP_COMB",
    "CANAL_COMB",
    "DED_LBL",
    "RI_ENTRY",
    "K_LBL",
    "OFFSET_LBL",
    "OBS_LBL",
    "FORCA_LBL",
    "COMPR_ENTRY",
    "ABA_EXT_LBL",
    "Z_EXT_LBL",
    "DED_ESPEC_ENTRY",
]

# Lista de widgets de entrada/input do cabeçalho (para captura de estado)
WIDGETS_ENTRADA_CABECALHO = [
    "MAT_COMB",
    "ESP_COMB",
    "CANAL_COMB",
    "COMPR_ENTRY",
    "RI_ENTRY",
    "DED_ESPEC_ENTRY",
]

# Prefixos para categorização de widgets de dobras
WIDGETS_DOBRAS = [
    "aba",
    "total_abas",
    "medidadobra",
    "metadedobra",
    "blank",
    "FRAME_DOBRA",
]

# Diretórios e arquivos de atualização
UPDATE_TEMP_DIR = os.path.join(BASE_DIR, "update_temp")

# Arquivo executável da aplicação principal
APP_EXECUTABLE_NAME = "Calculadora de Dobra.exe"
APP_EXECUTABLE_PATH = os.path.join(BASE_DIR, APP_EXECUTABLE_NAME)


def ensure_dirs_exist() -> None:
    """
    Garante que todos os diretórios essenciais para a aplicação existam.
    """
    os.makedirs(DATABASE_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(CACHE_DIR, exist_ok=True)
    # Diretórios de IPC são criados pelo ipc_manager


# Garante a criação dos diretórios na importação do módulo.
ensure_dirs_exist()


# --- 2. FUNÇÕES UTILITÁRIAS ---


def _normalize_text(text: str) -> str:
    """
    Remove espaços em branco das bordas e caracteres invisíveis (como ZWSP),
    mas PRESERVA quebras de linha e tabulações importantes para formatação.
    """
    if not text:
        return ""

    # Normaliza e remove caracteres de controle e formato (incluindo ZWSP)
    # ZWSP é \u200B, Categoria Cf (Format).
    # Cc (Control) inclui \n e \t, por isso precisamos salvá-los.

    safe_chars = {"\n", "\r", "\t"}

    try:
        normalized = "".join(
            ch
            for ch in unicodedata.normalize("NFC", text)
            if (unicodedata.category(ch) not in ("Cf", "Cc", "Cs"))
            or (ch in safe_chars)
        )
    except TypeError:
        # Fallback se o texto for inválido
        normalized = text

    # Remove espaços em branco normais das bordas
    return normalized.strip()


def aplicar_medida_borda_espaco(
    layout_ou_widget: Union[QLayout, QWidget],
    margem: int = MARGEM_PADRAO,
    espaco: int = ESPACAMENTO_PADRAO,
) -> None:
    """Aplica margens e espaçamento a um layout ou widget."""
    if hasattr(layout_ou_widget, "setContentsMargins"):
        layout_ou_widget.setContentsMargins(margem, margem, margem, margem)
    if hasattr(layout_ou_widget, "setSpacing"):
        layout_ou_widget.setSpacing(espaco)
    elif hasattr(layout_ou_widget, "layout") and layout_ou_widget.layout():
        layout = layout_ou_widget.layout()
        if layout and hasattr(layout, "setContentsMargins"):
            layout.setContentsMargins(margem, margem, margem, margem)
        if layout and hasattr(layout, "setSpacing"):
            layout.setSpacing(espaco)


def formatar_valor(v: Optional[float], precision: int = 4) -> str:
    """Formata um valor numérico com precisão especificada.

    Retorna string vazia para `None`. Tratamento seguro para tipos inválidos.
    """
    if v is None:
        return ""
    try:
        return f"{v:.{precision}f}"
    except (TypeError, ValueError):
        return str(v)


def tem_configuracao_dobras_valida():
    """Verifica se as configurações de dobras estão disponíveis.

    Returns:
        bool: True se VALORES_W e N estão definidos em globals
    """
    return hasattr(g, "VALORES_W") and hasattr(g, "N")


def ask_string(
    title: str, prompt: str, parent: Optional[QWidget] = None
) -> Optional[str]:
    """Pede uma string usando QInputDialog."""
    text, ok = QInputDialog.getText(parent, title, prompt, QLineEdit.EchoMode.Normal)
    return text if ok else None


def marcar_widget_como_sistema(widget: QWidget) -> None:
    """Atribui a flag que indica que o widget não deve ser manipulado pelo monitor."""
    setattr(widget, SYSTEM_WIDGET_ATTR, True)


def _show_message_box(
    icon: QMessageBox.Icon,
    title: str,
    message: Union[str, tuple],
    parent: Optional[QWidget] = None,
) -> None:
    """
    Cria e exibe uma QMessageBox, dividindo a mensagem em texto principal e informativo.
    """
    from .themed_widgets import (  # pylint: disable=import-outside-toplevel
        ThemedMessageBox,
    )

    msg = ThemedMessageBox(parent)
    msg.setIcon(icon)
    msg.setWindowTitle(title)

    main_text_raw = ""
    informative_text_raw = ""

    if isinstance(message, (list, tuple)):
        # Se for uma tupla/lista, assume-se (principal, informativo)
        main_text_raw = str(message[0]) if message and len(message) > 0 else ""
        informative_text_raw = str(message[1]) if len(message) > 1 else ""
    elif message is None:
        main_text_raw = ""
        informative_text_raw = ""
    else:
        # Se for uma string, divide na primeira quebra de linha
        parts = str(message).split("\n", 1)
        main_text_raw = parts[0]
        if len(parts) > 1:
            informative_text_raw = parts[1]

    # --- NOVO AJUSTE ---
    # Normaliza e limpa os textos para remover caracteres invisíveis
    # mas agora mantendo as quebras de linha
    main_text_limpo = _normalize_text(main_text_raw)
    informative_text_limpo = _normalize_text(informative_text_raw)

    # Aplica fallback se o texto principal estiver vazio APÓS a limpeza
    if not main_text_limpo:
        fallbacks = {
            QMessageBox.Icon.Critical: "Ocorreu um erro.",
            QMessageBox.Icon.Information: "Informação.",
        }
        if icon == QMessageBox.Icon.Warning:
            main_text_limpo = (
                "Ocorreu um erro." if "erro" in title.lower() else "Aviso."
            )
        else:
            main_text_limpo = fallbacks.get(icon, "Operação concluída.")
    # --- FIM DO AJUSTE ---

    msg.setText(main_text_limpo)
    if informative_text_limpo:
        msg.setInformativeText(informative_text_limpo)

    # Garante que o monitor de janelas não altere o diálogo
    marcar_widget_como_sistema(msg)

    if Janela.get_on_top_state():
        msg.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

    msg.exec()


def show_error(
    title: str, message: Union[str, tuple], parent: Optional[QWidget] = None
) -> None:
    """Mostra uma mensagem de erro usando QMessageBox."""
    _show_message_box(QMessageBox.Icon.Critical, title, message, parent)


def show_info(title: str, message: str, parent: Optional[QWidget] = None) -> None:
    """Mostra uma mensagem de informação usando QMessageBox."""
    _show_message_box(QMessageBox.Icon.Information, title, message, parent)


def show_warning(title: str, message: str, parent: Optional[QWidget] = None) -> None:
    """Mostimra uma mensagem de aviso usando QMessageBox."""
    _show_message_box(QMessageBox.Icon.Warning, title, message, parent)


def show_timed_message_box(parent, title, message, timeout_ms=10000):
    """Mostra uma caixa de mensagem com timeout automático."""
    from .themed_widgets import (  # pylint: disable=import-outside-toplevel
        ThemedMessageBox,
    )

    msg_box = ThemedMessageBox(
        QMessageBox.Icon.Information,
        title,
        message,
        QMessageBox.StandardButton.Ok,
        parent,
    )

    # Adiciona fallback se a mensagem estiver vazia (após limpeza)
    if not _normalize_text(message):
        msg_box.setText("Operação concluída.")

    # Timer para fechar automaticamente
    timer = QTimer(parent)
    timer.timeout.connect(msg_box.accept)
    timer.setSingleShot(True)
    timer.start(timeout_ms)

    # Mostrar diálogo (modal)
    msg_box.exec()

    # Parar timer se ainda rodando
    timer.stop()


def _resolve_executable(executable: str) -> str:
    """Resolve o caminho absoluto de um executável conhecido."""
    if os.path.isabs(executable):
        return executable
    resolved_path = shutil.which(executable)
    if not resolved_path:
        raise FileNotFoundError(f"Executável '{executable}' não encontrado no PATH.")
    return resolved_path


def run_trusted_command(
    command: Sequence[str],
    *,
    description: str,
    check: bool = True,
    **kwargs,
):
    """Executa comandos externos conhecidos após validações básicas."""
    if not command:
        raise ValueError("Comando externo não pode ser vazio.")

    executable, *args = command
    resolved_executable = _resolve_executable(executable)
    normalized_args = [str(arg) for arg in args]
    LOGGER.debug(
        "Executando comando confiável (%s): %s %s",
        description,
        resolved_executable,
        " ".join(normalized_args),
    )
    return subprocess.run(  # nosec B603 - comando controlado e validado
        [resolved_executable, *normalized_args],
        check=check,
        **kwargs,
    )


def open_file_with_default_app(file_path: str) -> None:
    """Abre um arquivo usando o aplicativo padrão do sistema operacional."""
    resolved_path = Path(file_path).expanduser().resolve(strict=True)

    if sys.platform == "win32":
        os.startfile(str(resolved_path))  # type: ignore[attr-defined]  # nosec B606
        # API nativa do Windows usada para abrir arquivos no aplicativo padrão.
    elif sys.platform == "darwin":
        run_trusted_command(
            ["open", str(resolved_path)], description="Abrir arquivo no macOS"
        )
    else:
        run_trusted_command(
            ["xdg-open", str(resolved_path)],
            description="Abrir arquivo em sistemas Unix",
        )


def ask_yes_no(
    title: str, message: Union[str, tuple], parent: Optional[QWidget] = None
) -> bool:
    """Pergunta sim/não usando QMessageBox."""
    from .themed_widgets import (  # pylint: disable=import-outside-toplevel
        ThemedMessageBox,
    )

    msg = ThemedMessageBox(parent)
    msg.setIcon(QMessageBox.Icon.Question)
    msg.setWindowTitle(title)
    msg.setWindowIcon(QIcon(ICON_PATH))

    # Aplicar a mesma lógica de _show_message_box para tratar a mensagem
    main_text_raw = ""
    informative_text_raw = ""

    if isinstance(message, (list, tuple)):
        main_text_raw = str(message[0]) if message and len(message) > 0 else ""
        informative_text_raw = str(message[1]) if len(message) > 1 else ""
    elif message is None:
        main_text_raw = ""
        informative_text_raw = ""
    else:
        parts = str(message).split("\n", 1)
        main_text_raw = parts[0]
        if len(parts) > 1:
            informative_text_raw = parts[1]

    # Limpa os textos
    main_text_limpo = _normalize_text(main_text_raw)
    informative_text_limpo = _normalize_text(informative_text_raw)

    # Fallback se vazio
    if not main_text_limpo:
        main_text_limpo = "Deseja continuar?"

    msg.setText(main_text_limpo)
    if informative_text_limpo:
        msg.setInformativeText(informative_text_limpo)

    msg.setStandardButtons(
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )

    # Renomeia botões
    msg.button(QMessageBox.StandardButton.Yes).setText("Sim")
    msg.button(QMessageBox.StandardButton.No).setText("Não")

    msg.setDefaultButton(QMessageBox.StandardButton.No)

    marcar_widget_como_sistema(msg)
    if Janela.get_on_top_state():
        msg.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

    return msg.exec() == QMessageBox.StandardButton.Yes


def setup_logging(log_filename: str, log_to_console: bool = True) -> None:
    """
    Configura o logging para arquivo e, opcionalmente, para o console.
    """
    try:
        log_filepath = os.path.join(LOG_DIR, log_filename)
        log_format = logging.Formatter(
            "%(asctime)s - [%(levelname)s] - %(filename)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        if logger.hasHandlers():
            logger.handlers.clear()

        file_handler = logging.handlers.RotatingFileHandler(
            log_filepath, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)

        if log_to_console:
            stream_handler = logging.StreamHandler(sys.stdout)
            stream_handler.setFormatter(log_format)
            logger.addHandler(stream_handler)

        logging.info("=" * 50)
        logging.info("Logging configurado. Arquivo de log em: %s", log_filepath)

    except (OSError, IOError) as e:
        logging.critical(
            "ERRO CRÍTICO: Não foi possível configurar o logging em arquivo: %s", e
        )
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )
        logging.error(
            "Falha ao inicializar o handler de arquivo de log.", exc_info=True
        )


# --- 3. EXPRESSÕES SIMPLES EM QLINEEDIT ---


def _resolver_no_ast(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_resolver_no_ast(node.operand)
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](
            _resolver_no_ast(node.left), _resolver_no_ast(node.right)
        )
    raise ValueError("Operacao nao permitida")


def _formatar_decimal(valor: float) -> str:
    texto = f"{valor:.4f}".rstrip("0").rstrip(".")
    texto = texto or "0"
    return texto.replace(".", ",")


def avaliar_expressao_para_texto(expr: str) -> Optional[str]:
    """Avalia expressão simples e devolve texto formatado com vírgula."""
    if not expr:
        return None

    sanitized = expr.replace(" ", "").replace(",", ".")
    if not any(op_char in sanitized for op_char in ["+", "-", "*", "/", "(", ")"]):
        return None
    if not re.fullmatch(r"[0-9.+\-*/()]*", sanitized):
        return None

    try:
        node = ast.parse(sanitized, mode="eval").body
        valor = _resolver_no_ast(node)
        return _formatar_decimal(valor)
    except (SyntaxError, ValueError, TypeError):
        return None


def resolver_expressao_no_line_edit(entry: QLineEdit) -> None:
    """Substitui o texto do QLineEdit pelo resultado, se a expressão for válida."""
    if entry is None:
        return
    texto_atual = entry.text()
    resultado = avaliar_expressao_para_texto(texto_atual)
    if resultado is None:
        return

    pos = entry.cursorPosition()
    entry.blockSignals(True)
    entry.setText(resultado)
    entry.setCursorPosition(min(pos, len(resultado)))
    entry.blockSignals(False)
