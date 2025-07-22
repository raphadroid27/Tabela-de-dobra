# -*- coding: utf-8 -*-
"""
Launcher da Aplicação de Cálculo de Dobra.

Responsável por:
1. Verificar a existência de novas versões da aplicação.
2. Forçar o encerramento seguro de todas as instâncias em execução.
3. Aplicar a atualização de forma atómica para evitar corrupção de ficheiros.
4. Iniciar a aplicação principal.
5. Gravar todas as operações num ficheiro de log.
"""

import json
import logging
import os
import shutil
import subprocess
import sys
import time
import zipfile
from datetime import datetime, timedelta
from typing import Tuple, Optional, Type

from semantic_version import Version
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, Session

# --- Configuração de Caminhos e Constantes ---

def get_base_dir() -> str:
    """Retorna o diretório base da aplicação, seja em modo script ou executável."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_dir()
APP_EXECUTABLE = "app.exe"
APP_PATH = os.path.join(BASE_DIR, APP_EXECUTABLE)
DB_DIR = os.path.join(BASE_DIR, "database")
DB_PATH = os.path.join(DB_DIR, "tabela_de_dobra.db")
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
UPDATES_DIR = os.path.join(BASE_DIR, 'updates')
VERSION_FILE_PATH = os.path.join(UPDATES_DIR, 'versao.json')

# Adiciona o diretório 'src' ao path para encontrar os modelos
sys.path.append(os.path.abspath(os.path.join(BASE_DIR, '.')))

# --- Importações de Módulos Locais ---
# As importações são feitas no topo para seguir as boas práticas (PEP 8)
try:
    from src.models.models import SystemControl
except ImportError as e:
    # Se a importação falhar, o launcher não pode funcionar.
    # Logamos o erro e saímos.
    logging.basicConfig(level=logging.CRITICAL)
    logging.critical("Falha CRÍTICA ao importar 'SystemControl': %s. PYTHONPATH está correto?", e)
    sys.exit(1)

# A versão deve ser mantida em sincronia com a versão em app.py
# A melhor prática seria ter um único ficheiro de versão partilhado.
LOCAL_APP_VERSION = "1.0.1"


# --- Funções do Launcher ---

def setup_logging() -> None:
    """Configura o sistema de logging para guardar em ficheiro e na consola."""
    os.makedirs(LOGS_DIR, exist_ok=True)
    log_file_path = os.path.join(LOGS_DIR, 'launcher.log')

    logging.basicConfig(
        level=logging.INFO,
        format='[LAUNCHER] %(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file_path, 'a', 'utf-8'),
            logging.StreamHandler(sys.stdout)
        ],
        force=True
    )

def get_db_session() -> Tuple[Optional[Session], Optional[Type[SystemControl]]]:
    """Cria e retorna uma sessão do SQLAlchemy para interagir com o banco."""
    if not os.path.exists(DB_PATH):
        logging.error("Base de dados não encontrada em: %s", DB_PATH)
        return None, None
    try:
        engine = create_engine(f'sqlite:///{DB_PATH}')
        session_factory = sessionmaker(bind=engine)
        return session_factory(), SystemControl
    except SQLAlchemyError as e:
        logging.error("Não foi possível conectar à base de dados: %s", e, exc_info=True)
        return None, None

def force_shutdown_all_instances(session: Session, model: Type[SystemControl]) -> bool:
    """Envia comando de desligamento e aguarda o fecho de todas as sessões."""
    logging.info("Enviando comando de desligamento para todas as instâncias...")
    try:
        cmd_entry = session.query(model).filter_by(key='UPDATE_CMD').first()
        if cmd_entry:
            cmd_entry.value = 'SHUTDOWN'
            cmd_entry.last_updated = datetime.utcnow()
            session.commit()

        logging.info("Aguardando o fecho das aplicações abertas...")
        start_time = time.time()
        while (time.time() - start_time) < 120:  # Timeout de 2 minutos
            timeout_threshold = datetime.utcnow() - timedelta(seconds=30)
            session.query(model).filter(
                model.type == 'SESSION',
                model.last_updated < timeout_threshold
            ).delete(synchronize_session=False)
            session.commit()

            active_sessions = session.query(model).filter_by(type='SESSION').count()
            logging.info("Sessões ativas restantes: %d", active_sessions)

            if active_sessions == 0:
                logging.info("Todas as instâncias foram fechadas com sucesso.")
                return True
            time.sleep(5)

        logging.error("Timeout! Algumas instâncias não fecharam a tempo.")
        return False
    except SQLAlchemyError as e:
        logging.error("Erro de base de dados ao forçar o desligamento: %s", e, exc_info=True)
        return False
    finally:
        try:
            cmd_entry = session.query(model).filter_by(key='UPDATE_CMD').first()
            if cmd_entry:
                cmd_entry.value = 'NONE'
                session.commit()
        except SQLAlchemyError:
            logging.error("Falha ao redefinir o comando de atualização.")

def check_for_updates() -> Tuple[bool, Optional[str]]:
    """Verifica se há uma nova versão da aplicação disponível."""
    logging.info("Versão local da aplicação: %s", LOCAL_APP_VERSION)
    logging.info("Verificando atualizações em: %s", VERSION_FILE_PATH)

    if not os.path.exists(VERSION_FILE_PATH):
        logging.warning("Ficheiro 'versao.json' não encontrado. A pular atualização.")
        return False, None

    try:
        with open(VERSION_FILE_PATH, 'r', encoding='utf-8') as f:
            server_info = json.load(f)
        server_version_str = server_info["versao"]
        download_url = server_info["url_download"]

        logging.info("Versão disponível no servidor: %s", server_version_str)

        if Version(server_version_str) > Version(LOCAL_APP_VERSION):
            logging.info("Nova versão encontrada!")
            return True, download_url

        logging.info("A sua aplicação já está atualizada.")
        return False, None
    except (json.JSONDecodeError, KeyError, TypeError, IOError) as e:
        logging.error("Erro ao ler o ficheiro de versão: %s", e, exc_info=True)
        return False, None

def _rollback_update(backup_dir: str, app_dir: str):
    """Restaura os ficheiros a partir do backup em caso de falha."""
    logging.info("...Iniciando rollback da atualização...")
    if not os.path.isdir(backup_dir):
        return
    try:
        for item in os.listdir(backup_dir):
            shutil.move(os.path.join(backup_dir, item), os.path.join(app_dir, item))
        logging.info("Rollback concluído. A versão anterior foi restaurada.")
    except (IOError, OSError) as e:
        logging.critical("ERRO CRÍTICO DURANTE O ROLLBACK: %s.", e, exc_info=True)

def apply_update(download_url: str) -> bool:
    """Baixa e aplica a atualização de forma atómica."""
    app_dir = os.path.dirname(APP_PATH)
    zip_path = os.path.join(UPDATES_DIR, download_url)
    temp_extract_dir = os.path.join(app_dir, "_temp_update")
    backup_dir = os.path.join(app_dir, "_backup")

    if not os.path.exists(zip_path):
        logging.error("Ficheiro de atualização não encontrado em %s", zip_path)
        return False

    try:
        logging.info("Extraindo ficheiros para pasta temporária: %s", temp_extract_dir)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_extract_dir)

        logging.info("Criando backup dos ficheiros antigos...")
        os.makedirs(backup_dir, exist_ok=True)
        for item in os.listdir(temp_extract_dir):
            old_path = os.path.join(app_dir, item)
            if os.path.exists(old_path):
                shutil.move(old_path, os.path.join(backup_dir, item))

        logging.info("Movendo novos ficheiros para o diretório da aplicação...")
        for item in os.listdir(temp_extract_dir):
            shutil.move(os.path.join(temp_extract_dir, item), os.path.join(app_dir, item))

        logging.info("Atualização aplicada com sucesso!")
        return True
    except (IOError, OSError, zipfile.BadZipFile) as e:
        logging.error("Erro ao aplicar a atualização: %s", e, exc_info=True)
        logging.warning("Permissão negada? Tente executar o launcher como Administrador.")
        _rollback_update(backup_dir, app_dir)
        return False
    finally:
        logging.info("Limpando ficheiros temporários...")
        shutil.rmtree(temp_extract_dir, ignore_errors=True)
        shutil.rmtree(backup_dir, ignore_errors=True)

def start_application():
    """Inicia a aplicação principal."""
    if not os.path.exists(APP_PATH):
        logging.error("Executável da aplicação não encontrado em: %s", APP_PATH)
        return
    logging.info("Iniciando a aplicação: %s", APP_PATH)
    try:
        subprocess.Popen([APP_PATH])
    except OSError as e:
        logging.error("Erro ao iniciar a aplicação: %s", e, exc_info=True)

def main() -> int:
    """Fluxo principal do Launcher."""
    setup_logging()
    logging.info("=" * 50)
    logging.info("Launcher iniciado.")
    logging.warning("A atualização pode exigir permissões de Administrador.")

    update_available, download_url = check_for_updates()

    if update_available and download_url:
        logging.info("Atualização encontrada. A preparar para instalar...")
        db_session, model = get_db_session()
        if not (db_session and model):
            logging.error("Não foi possível conectar à BD. Atualização cancelada.")
        else:
            try:
                if force_shutdown_all_instances(db_session, model):
                    if apply_update(download_url):
                        logging.info("Processo de atualização finalizado com sucesso.")
                    else:
                        logging.error("Falha ao aplicar a atualização. Versão anterior mantida.")
                else:
                    logging.error("Não foi possível fechar instâncias. Atualização cancelada.")
            finally:
                db_session.close()

    start_application()
    logging.info("Launcher finalizado.")
    logging.info("=" * 50)
    logging.shutdown()
    return 0

if __name__ == "__main__":
    sys.exit(main())
