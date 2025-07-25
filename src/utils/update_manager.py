"""
Módulo para Gerenciamento de Atualizações da Aplicação.

Responsável por:
- Verificar a existência de novas versões em um repositório local.
- Baixar o arquivo de atualização para uma pasta temporária.
- Sinalizar ao launcher que uma atualização está pronta para ser instalada.
"""

import os
import sys
import json
import shutil
import logging
from typing import Optional, Dict, Any
from semantic_version import Version

# --- Configuração de Caminhos de Forma Robusta ---


def get_base_dir() -> str:
    """Retorna o diretório base da aplicação, seja em modo script ou executável."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    # No ambiente de desenvolvimento, assume que este arquivo está em 'src/utils',
    # e o diretório base está dois níveis acima.
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


# --- Constantes Globais ---
BASE_DIR = get_base_dir()
UPDATES_DIR = os.path.join(BASE_DIR, 'updates')
UPDATE_TEMP_DIR = os.path.join(BASE_DIR, 'update_temp')
VERSION_FILE_PATH = os.path.join(UPDATES_DIR, 'versao.json')
UPDATE_FLAG_FILE = os.path.join(BASE_DIR, 'update_pending.flag')


def check_for_updates(current_version_str: str) -> Optional[Dict[str, Any]]:
    """
    Verifica se há uma nova versão comparando com o arquivo versao.json.

    Args:
        current_version_str: A versão atual da aplicação (ex: "2.2.0").

    Returns:
        Um dicionário com informações da nova versão se houver uma, caso contrário None.
    """
    if not os.path.exists(VERSION_FILE_PATH):
        logging.warning(
            "Arquivo 'versao.json' não encontrado. Pulando verificação de atualização.")
        return None

    try:
        with open(VERSION_FILE_PATH, 'r', encoding='utf-8') as f:
            server_info = json.load(f)

        latest_version_str = server_info.get("ultima_versao")
        if not latest_version_str:
            logging.error(
                "Chave 'ultima_versao' não encontrada no versao.json.")
            return None

        if Version(latest_version_str) > Version(current_version_str):
            logging.info("Nova versão encontrada: %s", latest_version_str)
            return server_info

        return None
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logging.error("Erro ao ler ou processar o arquivo de versão: %s", e)
        return None
    except (IOError, OSError) as e:
        logging.error(
            "Erro inesperado de I/O ao verificar atualizações: %s", e)
        return None


def download_update(nome_arquivo: str) -> None:
    """
    "Baixa" (copia) o arquivo de atualização do repositório 'updates'
    para a pasta temporária 'update_temp'.

    Args:
        nome_arquivo: O nome do arquivo .zip da atualização.

    Raises:
        FileNotFoundError: Se o arquivo de origem não for encontrado.
        IOError: Se houver um erro ao copiar o arquivo.
    """
    source_path = os.path.join(UPDATES_DIR, nome_arquivo)
    if not os.path.exists(source_path):
        raise FileNotFoundError(
            f"Arquivo de atualização '{nome_arquivo}' não encontrado no diretório 'updates'.")

    os.makedirs(UPDATE_TEMP_DIR, exist_ok=True)
    destination_path = os.path.join(UPDATE_TEMP_DIR, nome_arquivo)

    try:
        shutil.copy(source_path, destination_path)
        logging.info("Arquivo de atualização '%s' copiado para '%s'.",
                     nome_arquivo, UPDATE_TEMP_DIR)
    except IOError as e:
        logging.error("Erro ao copiar o arquivo de atualização: %s", e)
        raise


def prepare_update_flag() -> None:
    """
    Cria um arquivo de sinalização ('update_pending.flag') para notificar
    o launcher que uma atualização deve ser instalada.
    """
    try:
        with open(UPDATE_FLAG_FILE, 'w', encoding='utf-8') as _:
            pass  # Cria um arquivo vazio
        logging.info("Sinalizador de atualização '%s' criado.",
                     UPDATE_FLAG_FILE)
    except IOError as e:
        logging.error(
            "Não foi possível criar o sinalizador de atualização: %s", e)
        raise


def get_update_info() -> Optional[Dict[str, Any]]:
    """
    Lê e retorna as informações do arquivo versao.json sem comparar versões.
    """
    if not os.path.exists(VERSION_FILE_PATH):
        return None
    try:
        with open(VERSION_FILE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, KeyError, IOError) as e:
        logging.error(
            "Erro ao ler informações de atualização do versao.json: %s", e)
        return None
