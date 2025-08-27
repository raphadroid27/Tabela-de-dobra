"""
Módulo para Gerenciamento de Atualizações da Aplicação.

Responsável por:
- Verificar a existência de novas versões através de uma ação manual.
- Exibir notificações sobre atualizações disponíveis com feedback de erro detalhado.
- Gerenciar a versão instalada no banco de dados.
"""

import json
import logging
import os
import shutil
from typing import Any, Dict, Optional, Tuple

from semantic_version import Version

from src.config import globals as g
from src.models.models import SystemControl
from src.utils.banco_dados import session_scope
from src.utils.utilitarios import (
    UPDATE_TEMP_DIR,
    UPDATES_DIR,
    VERSION_FILE_PATH,
    show_error,
    show_info,
)


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


def _ensure_version_file_exists() -> bool:
    """
    Garante que o arquivo versao.json exista. Se não existir, cria um com valores padrão.
    """
    if not os.path.exists(VERSION_FILE_PATH):
        logging.warning("Arquivo 'versao.json' não encontrado. Criando um novo.")
        try:
            # Garante que o diretório 'updates' exista
            os.makedirs(UPDATES_DIR, exist_ok=True)
            default_data = {
                "ultima_versao": "1.0.0",
                "nome_arquivo": "update-1.0.0.zip",
                "notas_versao": "Versão inicial.",
            }
            with open(VERSION_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(default_data, f, indent=4)
            logging.info("Arquivo 'versao.json' criado com sucesso com a versão 1.0.0.")
        except (IOError, OSError) as e:
            logging.error("Não foi possível criar o arquivo 'versao.json': %s", e)
            return False
    return True


def checar_updates(current_version_str: str) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Verifica se há uma nova versão comparando com o arquivo versao.json.

    Args:
        current_version_str: A versão atual da aplicação (ex: "2.2.0").

    Returns:
        Uma tupla (status, data), onde status pode ser:
        'success': Nova versão encontrada, data contém as informações.
        'no_update': Nenhuma nova versão, data é None.
        'not_found': Arquivo de versão não encontrado (obsoleto, mas mantido por segurança).
        'error': Ocorreu um erro, data contém a mensagem de erro.
    """
    if not current_version_str:
        logging.error("Versão atual não fornecida para checagem.")
        return "error", {"message": "Versão atual não fornecida."}

    if not _ensure_version_file_exists():
        return "error", {
            "message": "Não foi possível criar ou acessar o arquivo de versão."
        }

    try:
        with open(VERSION_FILE_PATH, "r", encoding="utf-8") as f:
            server_info = json.load(f)

        latest_version_str = server_info.get("ultima_versao")
        if not latest_version_str:
            logging.error("Chave 'ultima_versao' não encontrada no versao.json.")
            return "error", {"message": "Arquivo de versão malformado."}

        if Version(latest_version_str) > Version(current_version_str):
            logging.info("Nova versão encontrada: %s", latest_version_str)
            return "success", dict(server_info)

        return "no_update", None
    except (json.JSONDecodeError, KeyError, ValueError, IOError, OSError) as e:
        logging.error("Erro ao ler ou processar o arquivo de versão: %s", e)
        return "error", {"message": f"Erro ao processar o arquivo de versão: {e}"}


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


def manipular_clique_update():
    """
    Gerencia o clique no botão de atualização, executando uma verificação
    manual e exibindo o resultado em um pop-up com feedback detalhado.
    """
    logging.info("Verificação manual de atualização iniciada pelo usuário.")

    current_version = get_installed_version()
    if not current_version:
        show_error(
            "Erro de Versão",
            "Não foi possível determinar a versão atual.",
            parent=g.PRINC_FORM,
        )
        return

    status, data = checar_updates(current_version)

    if status == "success":
        latest_version = data.get("ultima_versao", "desconhecida")
        show_info(
            "Atualização Disponível",
            f"Uma nova versão ({latest_version}) está disponível!\n"
            "Use a ferramenta de administração para atualizar.",
            parent=g.PRINC_FORM,
        )
    elif status == "no_update":
        show_info(
            "Nenhuma Atualização",
            "O seu aplicativo já está atualizado.",
            parent=g.PRINC_FORM,
        )
    elif status == "not_found":
        # Este caso agora é menos provável, mas mantido por segurança.
        show_error(
            "Erro de Conexão",
            "Não foi possível conectar ao servidor de atualizações.\n"
            "Verifique sua conexão ou tente mais tarde.",
            parent=g.PRINC_FORM,
        )
    elif status == "error":
        error_message = data.get("message", "Ocorreu um erro desconhecido.")
        show_error(
            "Erro na Verificação",
            f"Ocorreu um erro ao verificar as atualizações:\n{error_message}",
            parent=g.PRINC_FORM,
        )
