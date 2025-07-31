# -*- coding: utf-8 -*-
"""
Módulo para Gerenciamento de Atualizações da Aplicação.

Responsável por:
- Verificar a existência de novas versões.
- Orquestrar o lançamento do updater.exe para lidar com o processo de atualização.
"""

import os
import json
import logging
import subprocess
import shutil
from typing import Optional, Dict, Any
from semantic_version import Version

from src.utils.utilitarios import (
    VERSION_FILE_PATH, show_error, obter_dir_base,
    UPDATES_DIR, UPDATE_TEMP_DIR
)
from src.config import globals as g

# --- Constantes ---
UPDATER_EXECUTABLE_NAME = "updater.exe"
UPDATER_EXECUTABLE_PATH = os.path.join(
    obter_dir_base(), UPDATER_EXECUTABLE_NAME)


def checar_updates(current_version_str: str) -> Optional[Dict[str, Any]]:
    """
    Verifica se há uma nova versão comparando com o arquivo versao.json.

    Args:
        current_version_str: A versão atual da aplicação (ex: "2.2.0").

    Returns:
        Um dicionário com informações da nova versão se houver uma, caso contrário None.
    """
    if not os.path.exists(VERSION_FILE_PATH):
        logging.warning(
            "Arquivo 'versao.json' não encontrado. Pulando verificação.")
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
    except (json.JSONDecodeError, KeyError, ValueError, IOError, OSError) as e:
        logging.error(
            "Erro ao ler ou processar o arquivo de versão: %s", e)
        return None


def download_update(nome_arquivo: str) -> None:
    """
    Copia o arquivo de atualização para a pasta temporária.
    Esta função é chamada pelo updater.py, que importa este módulo.
    """
    source_path = os.path.join(UPDATES_DIR, nome_arquivo)
    if not os.path.exists(source_path):
        raise FileNotFoundError(
            f"Arquivo de atualização '{nome_arquivo}' não encontrado.")

    os.makedirs(UPDATE_TEMP_DIR, exist_ok=True)
    destination_path = os.path.join(UPDATE_TEMP_DIR, nome_arquivo)
    shutil.copy(source_path, destination_path)
    logging.info("Arquivo '%s' copiado para '%s'.",
                 nome_arquivo, UPDATE_TEMP_DIR)


def checagem_periodica_update(versao_atual: str):
    """Verifica periodicamente se há atualizações e atualiza a UI."""
    logging.info("Verificando atualizações em segundo plano...")
    update_info = checar_updates(versao_atual)
    if update_info:
        logging.info("Nova versão encontrada: %s",
                     update_info.get('ultima_versao'))
        g.UPDATE_INFO = update_info
        _atualizar_ui_conforme_status(True)
    else:
        logging.info("Nenhuma nova atualização encontrada.")
        g.UPDATE_INFO = None
        _atualizar_ui_conforme_status(False)


def manipular_clique_update():
    """
    Gerencia o clique no botão de atualização, lançando o updater.exe.
    """
    if not os.path.exists(UPDATER_EXECUTABLE_PATH):
        show_error("Erro",
                   f"O atualizador ({UPDATER_EXECUTABLE_NAME}) não foi "
                   "encontrado na pasta do aplicativo.",
                   parent=g.PRINC_FORM)
        return

    argumento = '--apply' if g.UPDATE_INFO else '--check'

    try:
        logging.info("Lançando o atualizador: %s %s",
                     UPDATER_EXECUTABLE_PATH, argumento)
        # pylint: disable=consider-using-with
        subprocess.Popen([UPDATER_EXECUTABLE_PATH, argumento])

    except OSError as e:
        logging.error("Falha ao iniciar o updater.exe: %s", e)
        show_error("Erro ao Lançar",
                   f"Não foi possível iniciar o processo de atualização.\n\nErro: {e}",
                   parent=g.PRINC_FORM)


def _atualizar_ui_conforme_status(update_available: bool):
    """Atualiza o texto e o estado do botão de atualização na UI principal."""
    if not hasattr(g, 'UPDATE_ACTION') or not g.UPDATE_ACTION:
        return

    if update_available:
        g.UPDATE_ACTION.setText("⬇️ Aplicar Atualização")
        tooltip_msg = (f"Versão {g.UPDATE_INFO.get('ultima_versao', '')} "
                       "disponível! Clique para atualizar.")
        g.UPDATE_ACTION.setToolTip(tooltip_msg)
    else:
        g.UPDATE_ACTION.setText("🔄 Verificar Atualizações")
        g.UPDATE_ACTION.setToolTip(
            "Verificar se há uma nova versão do aplicativo.")
