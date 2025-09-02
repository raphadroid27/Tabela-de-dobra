"""
Módulo para Gerenciamento de Atualizações da Aplicação.

Responsável por:
- Gerenciar a versão instalada no banco de dados.
- Conter a lógica para aplicar um pacote de atualização.
"""

import logging
import os
import shutil
import subprocess
import time
import zipfile
from typing import Callable, Optional

from sqlalchemy.exc import SQLAlchemyError

from src.models.models import SystemControl
from src.utils.banco_dados import get_session
from src.utils.session_manager import force_shutdown_all_instances
from src.utils.utilitarios import (
    APP_EXECUTABLE_PATH,
    UPDATE_TEMP_DIR,
    obter_dir_base,
    show_error,
)


def get_installed_version() -> Optional[str]:
    """Lê a versão atualmente instalada a partir do banco de dados."""
    try:
        with get_session() as session:
            version_entry = (
                session.query(SystemControl).filter_by(key="INSTALLED_VERSION").first()
            )
            if version_entry:
                logging.info(
                    "Versão instalada encontrada no DB: %s", version_entry.value
                )
                return str(version_entry.value) if version_entry.value else None
        logging.warning(
            "Nenhuma entrada 'INSTALLED_VERSION' encontrada no banco de dados."
        )
        return None
    except SQLAlchemyError as e:
        logging.error("Não foi possível ler a versão do DB: %s", e)
        return None


def set_installed_version(version: str):
    """Grava ou atualiza a versão instalada no banco de dados."""
    try:
        with get_session() as session:
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
    except SQLAlchemyError as e:
        logging.error("Não foi possível gravar a versão no DB: %s", e)


def _apply_update(zip_filename: str) -> bool:
    """Aplica a atualização extraindo os arquivos."""
    zip_filepath = os.path.join(UPDATE_TEMP_DIR, zip_filename)
    if not os.path.exists(zip_filepath):
        return False
    app_dir = obter_dir_base()
    try:
        extract_path = os.path.join(UPDATE_TEMP_DIR, "extracted")
        if os.path.exists(extract_path):
            shutil.rmtree(extract_path)
        os.makedirs(extract_path, exist_ok=True)
        with zipfile.ZipFile(zip_filepath, "r") as zip_ref:
            zip_ref.extractall(extract_path)

        for item in os.listdir(extract_path):
            src = os.path.join(extract_path, item)
            dst = os.path.join(app_dir, item)
            try:
                if os.path.isdir(dst):
                    shutil.rmtree(dst)
                elif os.path.isfile(dst):
                    os.remove(dst)
                shutil.move(src, dst)
            except OSError as e:
                logging.warning("Não foi possível substituir '%s': %s.", item, e)
        return True
    except (IOError, OSError, zipfile.BadZipFile) as e:
        logging.error("Erro ao aplicar a atualização: %s", e)
        return False
    finally:
        if os.path.isdir(UPDATE_TEMP_DIR):
            try:
                shutil.rmtree(UPDATE_TEMP_DIR)
            except OSError as e:
                logging.error("Não foi possível remover o diretório temporário: %s", e)


def _start_application():
    """Inicia a aplicação principal após a atualização."""
    if not os.path.exists(APP_EXECUTABLE_PATH):
        show_error(
            "Erro Crítico",
            f"Executável principal não encontrado:\n{APP_EXECUTABLE_PATH}",
        )
        return
    logging.info("Iniciando a aplicação: %s", APP_EXECUTABLE_PATH)
    try:
        subprocess.Popen([APP_EXECUTABLE_PATH])  # pylint: disable=R1732
    except OSError as e:
        show_error("Erro ao Reiniciar", f"Não foi possível reiniciar a aplicação:\n{e}")


def run_update_process(
    selected_file_path: str, progress_callback: Callable[[str, int], None]
):
    """Executa o processo completo de atualização."""
    zip_filename = os.path.basename(selected_file_path)

    progress_callback("Copiando arquivo de atualização...", 10)
    try:
        if os.path.exists(UPDATE_TEMP_DIR):
            shutil.rmtree(UPDATE_TEMP_DIR)
        os.makedirs(UPDATE_TEMP_DIR, exist_ok=True)
        shutil.copy(selected_file_path, UPDATE_TEMP_DIR)
    except (IOError, OSError) as e:
        raise IOError(f"Falha ao copiar o arquivo de atualização: {e}") from e

    progress_callback("Fechando a aplicação principal...", 40)
    time.sleep(3)

    try:

        def shutdown_progress_wrapper(active_sessions: int):
            progress_callback(f"Aguardando {active_sessions} instância(s)...", 50)

        if not force_shutdown_all_instances(shutdown_progress_wrapper):
            raise RuntimeError("Não foi possível fechar as instâncias da aplicação.")
    except Exception as e:
        raise ConnectionError(f"Falha ao tentar fechar as instâncias: {e}") from e

    progress_callback("Aplicando a atualização...", 70)
    if not _apply_update(zip_filename):
        raise IOError("Falha ao aplicar os arquivos de atualização.")

    progress_callback("Atualização concluída! Reiniciando...", 90)
    time.sleep(2)
    _start_application()
    progress_callback("Concluído!", 100)
