"""
Módulo para Gerenciamento de Atualizações da Aplicação.

Responsável por:
- Verificar a existência de novas versões em um repositório local.
- Baixar o arquivo de atualização para uma pasta temporária.
- Sinalizar ao launcher que uma atualização está pronta para ser instalada.
"""

import os
import json
import shutil
import logging
from typing import Optional, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
from PySide6.QtWidgets import QMessageBox, QApplication
from PySide6.QtCore import Qt
from semantic_version import Version
from src.utils.utilitarios import (
    VERSION_FILE_PATH, UPDATE_FLAG_FILE,
    UPDATES_DIR, UPDATE_TEMP_DIR, show_info, show_error)
from src.utils.usuarios import tem_permissao
from src.config import globals as g
from src.utils.banco_dados import session as db_session
from src.models.models import SystemControl


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

# --- Funções de Atualização ---


def checagem_periodica_update(versao_atual: str):
    """Verifica periodicamente se há atualizações disponíveis."""
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
    """Gerencia o clique no botão de atualização."""
    if g.UPDATE_INFO:
        if not tem_permissao('usuario', 'admin', show_message=False):
            msg = (f"Uma nova versão ({g.UPDATE_INFO.get('ultima_versao', 'N/A')}) "
                   "está disponível.\n\nPor favor, peça a um administrador para "
                   "fazer o login e aplicar a atualização.")
            show_info("Permissão Necessária", msg, parent=g.PRINC_FORM)
            return

        msg_admin = (f"Uma nova versão ({g.UPDATE_INFO.get('ultima_versao', 'N/A')}) "
                     "está disponível.\n\nDeseja preparar a atualização? O sistema "
                     "notificará todos os usuários para salvar seu trabalho e "
                     "fechar o aplicativo.")
        reply = QMessageBox.question(g.PRINC_FORM, "Confirmar Atualização", msg_admin,
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            _iniciar_processo_update()
    else:
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            logging.info("Verificação manual de atualização iniciada.")
            QApplication.processEvents()
            checagem_periodica_update(None)
        finally:
            QApplication.restoreOverrideCursor()

        if g.UPDATE_INFO:
            msg_found = (f"A versão {g.UPDATE_INFO.get('ultima_versao', 'N/A')} "
                         "está disponível!")
            show_info("Atualização Encontrada", msg_found, parent=g.PRINC_FORM)
        else:
            show_info("Verificar Atualizações",
                      "Você já está usando a versão mais recente.", parent=g.PRINC_FORM)


def _iniciar_processo_update():
    """Baixa, prepara o flag e dispara o comando de shutdown."""
    QApplication.setOverrideCursor(Qt.WaitCursor)
    try:
        logging.info("Iniciando processo de atualização: baixando arquivos...")
        QApplication.processEvents()
        download_update(g.UPDATE_INFO['nome_arquivo'])
        prepare_update_flag()
        cmd_entry = db_session.query(
            SystemControl).filter_by(key='UPDATE_CMD').first()
        if cmd_entry:
            cmd_entry.value = 'SHUTDOWN'
            db_session.commit()
        logging.info("Comando SHUTDOWN enviado para o banco de dados.")
        msg_success = ("A atualização foi preparada. Ela será instalada na próxima "
                       "vez que o programa for iniciado.\nO aplicativo será "
                       "encerrado em breve.")
        QMessageBox.information(g.PRINC_FORM, "Sucesso", msg_success)
    except (FileNotFoundError, IOError, SQLAlchemyError, KeyError) as e:
        logging.error("Erro ao iniciar o processo de atualização: %s", e)
        show_error("Erro de Atualização",
                   f"Não foi possível preparar a atualização: {e}", parent=g.PRINC_FORM)
    finally:
        QApplication.restoreOverrideCursor()


def _atualizar_ui_conforme_status(update_available: bool):
    """Atualiza o texto e o estado do botão de atualização."""
    if not hasattr(g, 'UPDATE_ACTION') or not g.UPDATE_ACTION:
        return
    if update_available:
        g.UPDATE_ACTION.setText("⬇️ Aplicar Atualização")
        tooltip_msg = f"Versão {g.UPDATE_INFO.get('ultima_versao', '')} disponível!"
        g.UPDATE_ACTION.setToolTip(tooltip_msg)
    else:
        g.UPDATE_ACTION.setText("🔄 Verificar Atualizações")
        g.UPDATE_ACTION.setToolTip(
            "Verificar se há uma nova versão do aplicativo.")
