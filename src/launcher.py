# -*- coding: utf-8 -*-
"""
Launcher da Aplicação de Cálculo de Dobra.

Responsável por:
1. Verificar se uma atualização foi autorizada (via arquivo .flag).
2. Se autorizada, forçar o encerramento seguro de todas as instâncias.
3. Aplicar a atualização.
4. Iniciar a aplicação principal.
"""

import sys
import os
import json
import subprocess
import zipfile
import time
import shutil
import logging
from datetime import datetime, timezone
from typing import Type
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from src.models.models import SystemControl as SystemControlModel
from src.utils.banco_dados import session_scope

# Importa os caminhos e funções do módulo utilitário centralizado
from src.utils.utilitarios import (
    setup_logging,
    BASE_DIR,
    APP_EXECUTABLE_PATH,
    UPDATE_TEMP_DIR,
    VERSION_FILE_PATH,
    UPDATE_FLAG_FILE
)

# --- Funções do Launcher ---


def force_shutdown_all_instances(session: Session, model: Type[SystemControlModel]) -> bool:
    """Envia comando de desligamento e aguarda o fechamento das sessões."""
    logging.info(
        "Enviando comando de desligamento para todas as instâncias...")
    try:
        cmd_entry = session.query(model).filter_by(key='UPDATE_CMD').first()
        if cmd_entry:
            cmd_entry.value = 'SHUTDOWN'
            cmd_entry.last_updated = datetime.now(timezone.utc)
            session.commit()

        logging.info("Aguardando o fechamento das aplicações abertas...")
        start_time = time.time()
        while (time.time() - start_time) < 180:  # Timeout de 3 minutos
            active_sessions = session.query(
                model).filter_by(type='SESSION').count()
            logging.info("Sessões ativas restantes: %s", active_sessions)

            if active_sessions == 0:
                logging.info("Todas as instâncias foram fechadas com sucesso.")
                time.sleep(3)  # Pausa para garantir liberação de arquivos
                return True
            time.sleep(5)

        logging.error("Timeout! Algumas instâncias não fecharam a tempo.")
        return False
    except SQLAlchemyError as e:
        logging.error("Erro ao forçar o desligamento: %s", e)
        session.rollback()
        return False
    finally:
        try:
            cmd_entry = session.query(model).filter_by(
                key='UPDATE_CMD').first()
            if cmd_entry and cmd_entry.value == 'SHUTDOWN':
                cmd_entry.value = 'NONE'
                session.commit()
        except SQLAlchemyError as e:
            logging.error("Erro ao limpar o comando de desligamento: %s", e)
            session.rollback()


def apply_update(zip_filename: str) -> bool:
    """Aplica a atualização a partir de um arquivo .zip."""
    zip_filepath = os.path.join(UPDATE_TEMP_DIR, zip_filename)
    if not os.path.exists(zip_filepath):
        logging.error(
            "Arquivo de atualização não encontrado em %s", zip_filepath)
        return False

    app_dir = BASE_DIR
    backup_dir = os.path.join(
        app_dir, f"_backup_{datetime.now().strftime('%Y%m%d%H%M%S')}")

    try:
        logging.info("Extraindo arquivos da atualização...")
        with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
            zip_ref.extractall(UPDATE_TEMP_DIR)
            update_files = [f for f in os.listdir(
                UPDATE_TEMP_DIR) if not f.endswith('.zip')]

        logging.info("Criando backup dos arquivos antigos...")
        os.makedirs(backup_dir, exist_ok=True)
        for item_name in update_files:
            old_item_path = os.path.join(app_dir, item_name)
            if os.path.exists(old_item_path):
                shutil.move(old_item_path, os.path.join(backup_dir, item_name))

        logging.info("Movendo novos arquivos para o diretório da aplicação...")
        for item_name in update_files:
            shutil.move(os.path.join(UPDATE_TEMP_DIR, item_name),
                        os.path.join(app_dir, item_name))

        logging.info("Atualização aplicada com sucesso!")
        return True
    except (IOError, OSError, zipfile.BadZipFile) as e:
        logging.error("Erro ao aplicar a atualização: %s", e)
        logging.warning(
            "Permissão negada? Tente executar o launcher como Administrador.")
        _rollback_update(backup_dir, app_dir)
        return False
    finally:
        logging.info("Limpando arquivos temporários...")
        if os.path.isdir(UPDATE_TEMP_DIR):
            shutil.rmtree(UPDATE_TEMP_DIR)
        if os.path.isdir(backup_dir):
            try:
                shutil.rmtree(backup_dir)
                logging.info("Backup temporário removido.")
            except OSError as e:
                logging.error(
                    "Não foi possível remover a pasta de backup: %s", e)


def _rollback_update(backup_dir: str, app_dir: str):
    """Restaura os arquivos a partir do backup em caso de falha."""
    logging.info("...Iniciando rollback da atualização...")
    if not os.path.isdir(backup_dir):
        logging.warning(
            "Diretório de backup não encontrado. Rollback impossível.")
        return
    try:
        for item in os.listdir(backup_dir):
            shutil.move(os.path.join(backup_dir, item),
                        os.path.join(app_dir, item))
        logging.info("Rollback concluído. A versão anterior foi restaurada.")
    except OSError as e:
        logging.critical("ERRO CRÍTICO DURANTE O ROLLBACK: %s.", e)


def start_application():
    """Inicia a aplicação principal (app.exe)."""
    if not os.path.exists(APP_EXECUTABLE_PATH):
        logging.error(
            "Executável da aplicação não encontrado em: %s", APP_EXECUTABLE_PATH)
        return
    logging.info("Iniciando a aplicação: %s", APP_EXECUTABLE_PATH)
    try:
        if sys.platform == "win32":
            with subprocess.Popen(
                    f'start /B "" "{APP_EXECUTABLE_PATH}"', shell=True) as proc:
                proc.communicate()

    except (OSError, ValueError) as e:
        logging.error("Erro ao iniciar a aplicação: %s", e)


def _perform_update_routine():
    """Contém a lógica completa para realizar a atualização."""
    logging.info("Sinalizador de atualização encontrado. Iniciando processo.")
    logging.warning("Este processo pode exigir permissões de Administrador.")

    try:
        with open(VERSION_FILE_PATH, 'r', encoding='utf-8') as f:
            update_info = json.load(f)
        zip_filename = update_info.get("nome_arquivo")

        if not zip_filename:
            logging.error(
                "Chave 'nome_arquivo' não encontrada no versao.json. Cancelando.")
            return

        with session_scope() as (db_session, model):
            if not db_session or not model:
                logging.error(
                    "Não foi possível conectar ao DB. A atualização foi cancelada.")
                return

            if force_shutdown_all_instances(db_session, model):
                if apply_update(zip_filename):
                    logging.info(
                        "Processo de atualização finalizado com sucesso.")
                    os.remove(UPDATE_FLAG_FILE)
                else:
                    logging.error(
                        "Falha ao aplicar a atualização. A versão anterior foi mantida.")
            else:
                logging.error(
                    "Não foi possível fechar todas as instâncias. A atualização foi cancelada.")

    except (FileNotFoundError, json.JSONDecodeError, KeyError, OSError, SQLAlchemyError) as e:
        logging.error("Erro crítico durante o processo de atualização: %s", e)
    finally:
        if os.path.exists(UPDATE_FLAG_FILE):
            logging.warning(
                "O sinalizador de atualização não foi removido. Removendo agora.")
            try:
                os.remove(UPDATE_FLAG_FILE)
            except OSError as e:
                logging.error(
                    "Não foi possível remover o sinalizador de atualização: %s", e)


def main() -> int:
    """Fluxo principal do Launcher."""
    setup_logging('launcher.log', log_to_console=True)
    logging.info("Launcher iniciado.")

    if os.path.exists(UPDATE_FLAG_FILE):
        _perform_update_routine()

    start_application()
    logging.info("Launcher finalizado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
