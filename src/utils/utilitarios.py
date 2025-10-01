"""Funções e constantes utilitárias genéricas para a aplicação.

Este módulo centraliza a gestão de caminhos, a configuração de logs e as
funções de diálogo com o usuário (QMessageBox, QInputDialog).
"""

import logging
import logging.handlers
import os
import shutil
import subprocess  # nosec B404 - integração controlada com ferramentas externas
import sys
from pathlib import Path
from typing import Optional, Sequence, Union

from PySide6.QtWidgets import QInputDialog, QLayout, QLineEdit, QMessageBox, QWidget

from src.config import globals as g

FILE_OPEN_EXCEPTIONS = (
    OSError,
    subprocess.SubprocessError,
    RuntimeError,
)


LOGGER = logging.getLogger(__name__)

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


def obter_dir_icone():
    """
    Retorna o caminho correto para o arquivo de ícone,
    considerando o modo de execução (normal ou empacotado).
    """
    if getattr(sys, "frozen", False):  # Verifica se está empacotado
        base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    else:
        base_path = os.path.abspath(".")  # Diretório atual no modo normal

    return os.path.join(base_path, "assets", "icone_2.ico")


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
RUNTIME_DIR = os.path.join(BASE_DIR, ".runtime")
SESSION_DIR = os.path.join(RUNTIME_DIR, "sessions")
COMMAND_DIR = os.path.join(RUNTIME_DIR, "commands")

# Cache movido para AppData
CACHE_DIR = os.path.join(APPDATA_DIR, "Calculadora de Dobra", "cache")


# Margens e espaçamentos padrão para layouts
MARGEM_PADRAO = 5
ESPACAMENTO_PADRAO = 5

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

# Arquivos de configuração do usuário (movido para AppData)
APPDATA_DIR = os.environ.get(
    "APPDATA", os.path.join(os.environ["USERPROFILE"], "AppData", "Roaming")
)
CONFIG_DIR = os.path.join(APPDATA_DIR, "Calculadora de Dobra")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


def ensure_dirs_exist() -> None:
    """
    Garante que todos os diretórios essenciais para a aplicação existam.
    """
    os.makedirs(DATABASE_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(CONFIG_DIR, exist_ok=True)
    os.makedirs(CACHE_DIR, exist_ok=True)
    # Diretórios de IPC são criados pelo ipc_manager


# Garante a criação dos diretórios na importação do módulo.
ensure_dirs_exist()


# --- 2. FUNÇÕES UTILITÁRIAS ---
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


def _show_message_box(
    icon: QMessageBox.Icon,
    title: str,
    message: Union[str, tuple],
    parent: Optional[QWidget] = None,
) -> None:
    """
    Cria e exibe uma QMessageBox, dividindo a mensagem em texto principal e informativo.
    """
    msg = QMessageBox(parent)
    msg.setIcon(icon)
    msg.setWindowTitle(title)

    main_text = ""
    informative_text = ""

    if isinstance(message, (list, tuple)):
        # Se for uma tupla/lista, assume-se (principal, informativo)
        main_text = str(message[0]) if message else ""
        informative_text = str(message[1]) if len(message) > 1 else ""
    else:
        # Se for uma string, divide na primeira quebra de linha
        parts = str(message).split("\n", 1)
        main_text = parts[0]
        if len(parts) > 1:
            informative_text = parts[1].strip()

    msg.setText(f"{main_text}")
    if informative_text:
        msg.setInformativeText(informative_text)

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
    """Mostra uma mensagem de aviso usando QMessageBox."""
    _show_message_box(QMessageBox.Icon.Warning, title, message, parent)


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
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Icon.Question)
    msg.setWindowTitle(title)

    # Aplicar a mesma lógica de _show_message_box para tratar a mensagem
    main_text = ""
    informative_text = ""

    if isinstance(message, (list, tuple)):
        # Se for uma tupla/lista, assume-se (principal, informativo)
        main_text = str(message[0]) if message else ""
        informative_text = str(message[1]) if len(message) > 1 else ""
    else:
        # Se for uma string, divide na primeira quebra de linha
        parts = str(message).split("\n", 1)
        main_text = parts[0]
        if len(parts) > 1:
            informative_text = parts[1].strip()

    msg.setText(f"{main_text}")
    if informative_text:
        msg.setInformativeText(informative_text)

    msg.setStandardButtons(
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )

    # Renomeia botões
    msg.button(QMessageBox.StandardButton.Yes).setText("Sim")
    msg.button(QMessageBox.StandardButton.No).setText("Não")

    msg.setDefaultButton(QMessageBox.StandardButton.No)
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
