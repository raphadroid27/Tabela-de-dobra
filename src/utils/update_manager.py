"""
Módulo para Gerenciamento de Atualizações da Aplicação.

Responsável por:
- Verificar a existência de novas versões.
- Orquestrar o lançamento do admin.exe para lidar com o processo de atualização.
- Gerenciar a versão instalada no banco de dados.
"""

import json
import logging
import os
import shutil
import subprocess  # nosec B404 - subprocess necessário para execução controlada do admin
from typing import Any, Dict, Optional

from semantic_version import Version

from src.config import globals as g
from src.models.models import SystemControl
from src.utils.banco_dados import session_scope
from src.utils.utilitarios import (
    UPDATE_TEMP_DIR,
    UPDATES_DIR,
    VERSION_FILE_PATH,
    obter_dir_base,
    show_error,
)

# --- MODIFICADO ---
ADMIN_EXECUTABLE_NAME = "admin.exe"  # Anteriormente UPDATER_EXECUTABLE_NAME
ADMIN_EXECUTABLE_PATH = os.path.join(obter_dir_base(), ADMIN_EXECUTABLE_NAME)


def get_installed_version() -> Optional[str]:
    """Lê a versão atualmente instalada a partir do banco de dados."""
    with session_scope() as (session, _):
        if not session:
            logging.error(
                "Não foi possível obter uma sessão do banco de dados para ler a versão."
            )
            return None
        version_entry = (
            session.query(SystemControl).filter_by(key="INSTALLED_VERSION").first()
        )
        if version_entry:
            logging.info("Versão instalada encontrada no DB: %s", version_entry.value)
            return str(version_entry.value) if version_entry.value else None
        logging.warning(
            "Nenhuma entrada 'INSTALLED_VERSION' encontrada no banco de dados."
        )
        return None


def set_installed_version(version: str):
    """Grava ou atualiza a versão instalada no banco de dados."""
    with session_scope() as (session, _):
        if not session:
            logging.error(
                "Não foi possível obter uma sessão do banco de dados para gravar a versão."
            )
            return
        version_entry = (
            session.query(SystemControl).filter_by(key="INSTALLED_VERSION").first()
        )
        if version_entry:
            if version_entry.value != version:
                logging.info(
                    "Atualizando a versão no DB de %s para %s",
                    version_entry.value,
                    version,
                )
                version_entry.value = str(version)
        else:
            logging.info("Gravando a versão inicial no DB: %s", version)
            new_entry = SystemControl(
                key="INSTALLED_VERSION", value=str(version), type="CONFIG"
            )
            session.add(new_entry)
        session.commit()


def checar_updates(current_version_str: str) -> Optional[Dict[str, Any]]:
    """
    Verifica se há uma nova versão comparando com o arquivo versao.json.

    Args:
        current_version_str: A versão atual da aplicação (ex: "2.2.0").

    Returns:
        Um dicionário com informações da nova versão se houver uma, caso contrário None.
    """
    if not current_version_str:
        logging.error("Versão atual não fornecida para checagem.")
        return None

    if not os.path.exists(VERSION_FILE_PATH):
        logging.warning("Arquivo 'versao.json' não encontrado. Pulando verificação.")
        return None

    try:
        with open(VERSION_FILE_PATH, "r", encoding="utf-8") as f:
            server_info = json.load(f)

        latest_version_str = server_info.get("ultima_versao")
        if not latest_version_str:
            logging.error("Chave 'ultima_versao' não encontrada no versao.json.")
            return None

        if Version(latest_version_str) > Version(current_version_str):
            logging.info("Nova versão encontrada: %s", latest_version_str)
            return dict(server_info)

        return None
    except (json.JSONDecodeError, KeyError, ValueError, IOError, OSError) as e:
        logging.error("Erro ao ler ou processar o arquivo de versão: %s", e)
        return None


def download_update(nome_arquivo: str) -> None:
    """
    Copia o arquivo de atualização para a pasta temporária.
    Esta função é chamada pelo admin.py, que importa este módulo.
    """
    source_path = os.path.join(UPDATES_DIR, nome_arquivo)
    if not os.path.exists(source_path):
        raise FileNotFoundError(
            f"Arquivo de atualização '{nome_arquivo}' não encontrado."
        )

    os.makedirs(UPDATE_TEMP_DIR, exist_ok=True)
    destination_path = os.path.join(UPDATE_TEMP_DIR, nome_arquivo)
    shutil.copy(source_path, destination_path)
    logging.info("Arquivo '%s' copiado para '%s'.", nome_arquivo, UPDATE_TEMP_DIR)


def checagem_periodica_update():
    """Verifica periodicamente se há atualizações e atualiza a UI."""
    logging.info("Verificando atualizações em segundo plano...")
    versao_atual = get_installed_version()  # Lê do DB
    if not versao_atual:
        return  # Não faz nada se não conseguir ler a versão

    update_info = checar_updates(versao_atual)
    if update_info:
        logging.info("Nova versão encontrada: %s", update_info.get("ultima_versao"))
        g.UPDATE_INFO = dict(update_info)
        _atualizar_ui_conforme_status(True)
    else:
        logging.info("Nenhuma nova atualização encontrada.")
        g.UPDATE_INFO = None
        _atualizar_ui_conforme_status(False)


def manipular_clique_update():
    """
    Gerencia o clique no botão de atualização, lançando o admin.exe.
    """
    # --- MODIFICADO ---
    if not os.path.exists(ADMIN_EXECUTABLE_PATH):
        show_error(
            "Erro",
            f"A ferramenta de administração ({ADMIN_EXECUTABLE_NAME}) não foi "
            "encontrada na pasta do aplicativo.",
            parent=g.PRINC_FORM,
        )
        return

    # O admin.exe sempre abre na tela de status do updater, então não precisa de argumento
    try:
        logging.info(
            "Lançando a ferramenta de administração: %s", ADMIN_EXECUTABLE_PATH
        )
        # pylint: disable=consider-using-with
        subprocess.Popen(
            [ADMIN_EXECUTABLE_PATH]
        )  # nosec B603 - executável validado do admin

    except OSError as e:
        logging.error("Falha ao iniciar o admin.exe: %s", e)
        show_error(
            "Erro ao Lançar",
            f"Não foi possível iniciar a ferramenta de administração.\n\nErro: {e}",
            parent=g.PRINC_FORM,
        )


def _atualizar_ui_conforme_status(update_available: bool):
    """Atualiza o texto e o estado do botão de atualização na UI principal."""
    if not hasattr(g, "UPDATE_ACTION") or not g.UPDATE_ACTION:
        return

    if update_available:
        g.UPDATE_ACTION.setText("⬇️ Abrir Ferramenta Admin")
        tooltip_msg = (
            f"Versão {g.UPDATE_INFO.get('ultima_versao', '')} "
            "disponível! Clique para abrir a ferramenta de admin e atualizar."
        )
        g.UPDATE_ACTION.setToolTip(tooltip_msg)
    else:
        g.UPDATE_ACTION.setText("⚙️ Abrir Ferramenta Admin")
        g.UPDATE_ACTION.setToolTip("Abrir a ferramenta de administração.")
