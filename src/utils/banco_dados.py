"""
Módulo utilitário para manipulação de banco de dados no aplicativo de Calculadora de Dobras.
Versão otimizada para múltiplas conexões simultâneas.
"""

import logging
import os
import shutil
import sqlite3
from typing import Optional
import datetime
import threading
from contextlib import contextmanager

from sqlalchemy import create_engine, event, pool
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import sessionmaker, scoped_session

from src.models.models import Base, Log, SystemControl
from src.utils.utilitarios import DB_PATH, DATABASE_DIR

# Pool de conexões otimizado para SQLite
engine = create_engine(
    f'sqlite:///{os.path.join(DATABASE_DIR, "tabela_de_dobra.db")}',
    poolclass=pool.StaticPool,
    connect_args={
        'timeout': 30,
        'check_same_thread': False,
        'isolation_level': None  # Autocommit mode
    },
    echo=False
)

# Event listener para otimizações SQLite


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):  # pylint: disable=unused-argument
    """Otimiza SQLite para múltiplas conexões."""
    cursor = dbapi_connection.cursor()

    # WAL mode para leituras simultâneas
    cursor.execute("PRAGMA journal_mode=WAL")

    # Otimizações de performance
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=10000")
    cursor.execute("PRAGMA temp_store=MEMORY")
    cursor.execute("PRAGMA mmap_size=268435456")  # 256MB
    cursor.execute("PRAGMA busy_timeout=30000")   # 30 segundos

    # Configurações WAL específicas
    cursor.execute("PRAGMA wal_autocheckpoint=1000")
    cursor.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    cursor.close()


# Session factory thread-safe
Session = scoped_session(sessionmaker(bind=engine))

# Lock global para operações críticas
_db_lock = threading.RLock()


@contextmanager
def get_db_session():
    """Context manager para sessões thread-safe."""
    db_session = Session()
    try:
        yield db_session
        db_session.commit()
    except (IntegrityError, OperationalError) as e:
        db_session.rollback()
        logging.error("Erro de banco de dados: %s", e)
        raise
    except Exception as e:
        db_session.rollback()
        logging.error("Erro inesperado no context manager: %s", e)
        raise
    finally:
        db_session.close()


def tratativa_erro():
    """
    Realiza o commit da sessão e trata erros de integridade e operacionais.
    """
    try:
        Session.commit()
    except (IntegrityError, OperationalError) as e:
        Session.rollback()
        logging.error("Erro de banco de dados: %s", e)
        raise
    except Exception as e:
        Session.rollback()
        logging.error("Erro inesperado: %s", e)
        raise


def registrar_log(usuario_nome, acao, tabela, registro_id, detalhes=None):
    """
    Registra uma ação no banco de dados de forma thread-safe.
    """
    with get_db_session() as db_session:
        try:
            log = Log(
                usuario_nome=usuario_nome,
                acao=acao,
                tabela=tabela,
                registro_id=registro_id,
                detalhes=detalhes,
            )
            db_session.add(log)
        except (IntegrityError, OperationalError) as e:
            logging.error("Erro de banco de dados ao criar log: %s", e)


def inicializar_banco_dados():
    """Cria as tabelas do banco de dados e registros iniciais, se necessário."""
    with _db_lock:
        logging.info("Inicializando o banco de dados e criando tabelas.")
        Base.metadata.create_all(engine)

        with get_db_session() as db_session:
            if not db_session.query(SystemControl).filter_by(key="UPDATE_CMD").first():
                logging.info(
                    "Inicializando o comando de atualização (UPDATE_CMD) no DB.")
                initial_command = SystemControl(
                    type="COMMAND", key="UPDATE_CMD", value="NONE"
                )
                db_session.add(initial_command)


def verificar_integridade_banco() -> bool:
    """Verifica a integridade do banco de dados."""
    try:
        with sqlite3.connect(DB_PATH, timeout=30) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check;")
            resultado = cursor.fetchone()
            return resultado[0] == "ok"
    except sqlite3.Error as e:
        logging.error("Erro ao verificar integridade: %s", e)
        return False
    except OSError as e:
        logging.error("Erro de acesso ao arquivo do banco: %s", e)
        return False


def otimizar_banco():
    """Executa otimizações periódicas no banco."""
    try:
        with sqlite3.connect(DB_PATH, timeout=30) as conn:
            cursor = conn.cursor()

            # Checkpoint WAL
            cursor.execute("PRAGMA wal_checkpoint(TRUNCATE)")

            # Vacuum se necessário
            cursor.execute("PRAGMA auto_vacuum=INCREMENTAL")
            cursor.execute("PRAGMA incremental_vacuum")

            # Análise de estatísticas
            cursor.execute("ANALYZE")

            logging.info("Otimização do banco concluída")

    except sqlite3.Error as e:
        logging.error("Erro ao otimizar banco: %s", e)


def criar_backup_automatico() -> Optional[str]:
    """Cria backup automático do banco."""
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(
            DATABASE_DIR, f"backup_tabela_de_dobra_{timestamp}.db"
        )

        # Backup usando WAL checkpoint
        with sqlite3.connect(DB_PATH, timeout=30) as conn:
            with sqlite3.connect(backup_path) as backup_conn:
                conn.backup(backup_conn)

        logging.info("Backup criado: %s", backup_path)
        return backup_path
    except (OSError, shutil.Error, sqlite3.Error) as e:
        logging.error("Erro ao criar backup: %s", e)
        return None


def fechar_conexoes():
    """Fecha todas as conexões de forma segura."""
    try:
        Session.remove()
        engine.dispose()
        logging.info("Conexões do banco fechadas")
    except (sqlite3.Error, OperationalError) as e:  # Mudança: captura específica
        logging.error("Erro ao fechar conexões do banco: %s", e)
    except OSError as e:  # Mudança: captura específica para erros de sistema
        logging.error("Erro de sistema ao fechar conexões: %s", e)
