"""
Launcher da Aplicação de Cálculo de Dobra.

Responsável por:
1. Verificar a existência de novas versões da aplicação a partir de uma pasta local.
2. Forçar o encerramento seguro de todas as instâncias em execução.
3. Aplicar a atualização de forma atômica para evitar corrupção de arquivos.
4. Iniciar a aplicação principal.

Este módulo foi projetado para ser executado como um executável independente.
"""

import sys
import os
import json
import subprocess
import zipfile
import time
import shutil
import logging
import logging.handlers
from datetime import datetime, timedelta
from typing import Tuple, Optional, Type

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from semantic_version import Version

# --- Configuração de Logging e Console ---
# Altere para False para desabilitar a saída de logs no console/terminal.
# Os logs sempre serão salvos no arquivo 'logs/launcher.log'.
LOG_TO_CONSOLE = True

# --- Configuração de Caminhos de Forma Robusta ---


def get_base_dir() -> str:
    """Retorna o diretório base da aplicação, seja em modo script ou executável."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


# --- Constantes e Caminhos Globais ---
BASE_DIR = get_base_dir()
APP_EXECUTABLE = "app.exe"
APP_PATH = os.path.join(BASE_DIR, APP_EXECUTABLE)
DB_DIR = os.path.join(BASE_DIR, "database")
DB_PATH = os.path.join(DB_DIR, "tabela_de_dobra.db")
UPDATES_DIR = os.path.join(BASE_DIR, 'updates')
VERSION_FILE_PATH = os.path.join(UPDATES_DIR, 'versao.json')
LOG_DIR = os.path.join(BASE_DIR, 'logs')

# Adiciona o diretório 'src' ao path para encontrar os modelos
sys.path.append(os.path.abspath(os.path.join(BASE_DIR, '.')))

# --- Configuração do Sistema de Logging ---


def setup_logging():
    """Configura o logging para arquivo e opcionalmente para o console."""
    os.makedirs(LOG_DIR, exist_ok=True)
    log_filepath = os.path.join(LOG_DIR, 'launcher.log')

    log_format = logging.Formatter(
        '%(asctime)s - [%(levelname)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Configura o logger principal
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Handler para salvar logs em arquivo com rotação
    # Cria um novo arquivo quando o atual atinge 1MB, mantém até 5 backups.
    file_handler = logging.handlers.RotatingFileHandler(
        log_filepath, maxBytes=1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)

    # Handler para exibir logs no console (se habilitado)
    if LOG_TO_CONSOLE:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(log_format)
        logger.addHandler(stream_handler)


# Importa o modelo e a versão APÓS a configuração do path
try:
    from src.models.models import SystemControl as SystemControlModel
    from src.app import APP_VERSION as LOCAL_APP_VERSION
except ImportError as e:
    # O logging pode não estar configurado aqui, então usamos print e saímos.
    print(
        f"ERRO CRÍTICO: Não foi possível importar módulos da aplicação: {e}")
    print("Verifique se o launcher está no diretório correto.")
    time.sleep(10)
    sys.exit(1)


# --- Funções do Launcher ---

def get_db_session() -> Tuple[Optional[Session], Optional[Type[SystemControlModel]]]:
    """
    Cria e retorna uma sessão do SQLAlchemy para interagir com o banco de dados.
    """
    if not os.path.exists(DB_PATH):
        logging.error("Banco de dados não encontrado em: %s", DB_PATH)
        return None, None
    try:
        engine = create_engine(f'sqlite:///{DB_PATH}')
        session_factory = sessionmaker(bind=engine)
        session = session_factory()
        return session, SystemControlModel
    except SQLAlchemyError as e:
        logging.error("Não foi possível conectar ao banco de dados: %s", e)
        return None, None


def force_shutdown_all_instances(
    session: Session, system_control_model: Type[SystemControlModel]
) -> bool:
    """
    Envia comando de desligamento e aguarda o fechamento de todas as sessões ativas.
    """
    logging.info(
        "Enviando comando de desligamento para todas as instâncias...")
    try:
        cmd_entry = session.query(system_control_model).filter_by(
            key='UPDATE_CMD').first()
        if cmd_entry:
            cmd_entry.value = 'SHUTDOWN'
            cmd_entry.last_updated = datetime.utcnow()
            session.commit()

        logging.info("Aguardando o fechamento das aplicações abertas...")
        start_time = time.time()
        while (time.time() - start_time) < 120:
            timeout_threshold = datetime.utcnow() - timedelta(seconds=30)
            session.query(system_control_model).filter(
                system_control_model.type == 'SESSION',
                system_control_model.last_updated < timeout_threshold
            ).delete(synchronize_session=False)
            session.commit()

            active_sessions = session.query(
                system_control_model).filter_by(type='SESSION').count()
            logging.info("Sessões ativas restantes: %s", active_sessions)

            if active_sessions == 0:
                logging.info("Todas as instâncias foram fechadas com sucesso.")
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
            cmd_entry = session.query(system_control_model).filter_by(
                key='UPDATE_CMD').first()
            if cmd_entry:
                cmd_entry.value = 'NONE'
                session.commit()
        except SQLAlchemyError as e:
            logging.error("Erro ao limpar o comando de desligamento: %s", e)
            session.rollback()


def check_for_updates() -> Tuple[bool, Optional[str]]:
    """
    Verifica se há uma nova versão da aplicação disponível na pasta 'updates'.
    """
    logging.info("Versão local do app: %s", LOCAL_APP_VERSION)
    logging.info("Verificando atualizações em: %s", VERSION_FILE_PATH)

    if not os.path.exists(VERSION_FILE_PATH):
        logging.info(
            "Arquivo 'versao.json' não encontrado. Pulando verificação.")
        return False, None

    try:
        with open(VERSION_FILE_PATH, 'r', encoding='utf-8') as f:
            server_info = json.load(f)

        server_version_str = server_info["versao"]
        download_filename = server_info["url_download"]
        logging.info("Versão disponível no servidor: %s", server_version_str)

        if Version(server_version_str) > Version(LOCAL_APP_VERSION):
            logging.info("Nova versão encontrada!")
            full_download_path = os.path.join(UPDATES_DIR, download_filename)
            logging.info("Caminho do arquivo de atualização: %s",
                         full_download_path)
            return True, full_download_path

        logging.info("Sua aplicação já está atualizada.")
        return False, None
    except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError) as e:
        logging.error("Erro ao verificar atualizações: %s", e)
        return False, None


def apply_update(zip_filepath: str) -> bool:
    """
    Aplica a atualização a partir de um arquivo .zip de forma atômica.
    """
    app_dir = BASE_DIR
    temp_extract_dir = os.path.join(app_dir, "_temp_update")
    backup_dir = os.path.join(app_dir, "_backup")

    if not os.path.exists(zip_filepath):
        logging.error(
            "Arquivo de atualização não encontrado em %s", zip_filepath)
        return False

    try:
        if os.path.isdir(temp_extract_dir):
            shutil.rmtree(temp_extract_dir)
        if os.path.isdir(backup_dir):
            shutil.rmtree(backup_dir)

        logging.info(
            "Extraindo arquivos para pasta temporária: %s", temp_extract_dir)
        os.makedirs(temp_extract_dir, exist_ok=True)
        with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
            zip_ref.extractall(temp_extract_dir)

        logging.info("Criando backup dos arquivos antigos...")
        os.makedirs(backup_dir, exist_ok=True)
        for item_name in os.listdir(temp_extract_dir):
            old_item_path = os.path.join(app_dir, item_name)
            if os.path.exists(old_item_path):
                shutil.move(old_item_path, os.path.join(backup_dir, item_name))

        logging.info("Movendo novos arquivos para o diretório da aplicação...")
        for item_name in os.listdir(temp_extract_dir):
            shutil.move(os.path.join(temp_extract_dir, item_name),
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
        if os.path.isdir(temp_extract_dir):
            shutil.rmtree(temp_extract_dir)
        if os.path.isdir(backup_dir):
            shutil.rmtree(backup_dir)


def _rollback_update(backup_dir: str, app_dir: str) -> None:
    """Restaura os arquivos a partir do backup em caso de falha na atualização."""
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
        logging.critical(
            "ERRO CRÍTICO DURANTE O ROLLBACK: %s. A instalação pode estar corrompida.", e
        )


def start_application() -> None:
    """Inicia a aplicação principal (app.exe)."""
    if not os.path.exists(APP_PATH):
        logging.error(
            "Executável da aplicação não encontrado em: %s", APP_PATH)
        return
    logging.info("Iniciando a aplicação: %s", APP_PATH)
    try:
        with subprocess.Popen([APP_PATH]):
            pass  # O processo é iniciado e o contexto é gerenciado
    except (OSError, ValueError) as e:
        logging.error("Erro ao iniciar a aplicação: %s", e)


def main() -> int:
    """Fluxo principal do Launcher."""
    setup_logging()
    logging.info("=" * 50)
    logging.info("Launcher iniciado.")
    logging.warning("A atualização pode exigir permissões de Administrador.")

    update_available, download_path = check_for_updates()

    if update_available and download_path:
        logging.info("Atualização encontrada. Preparando para instalar...")
        db_session, model = get_db_session()
        if not db_session:
            logging.error(
                "Não foi possível conectar ao DB. A atualização foi cancelada.")
        else:
            if force_shutdown_all_instances(db_session, model):
                if apply_update(download_path):
                    logging.info(
                        "Processo de atualização finalizado com sucesso.")
                else:
                    logging.error(
                        "Falha ao aplicar a atualização. A versão anterior foi mantida.")
            else:
                logging.error(
                    "Não foi possível fechar todas as instâncias do app. "
                    "A atualização foi cancelada."
                )
            db_session.close()

    start_application()
    logging.info("Launcher finalizado.")
    logging.info("=" * 50)
    time.sleep(3)
    return 0


if __name__ == "__main__":
    sys.exit(main())
