"""
Módulo utilitário para manipulação de banco de dados no aplicativo de Calculadora de Dobras.
Versão refatorada para usar sessões de curta duração (short-lived sessions)
e modo WAL (Write-Ahead Logging) para prevenir bloqueios de banco de dados.
"""

import logging
import os
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import sessionmaker

from src.models.models import Base, Log

# Garante que o diretório do banco de dados exista
DATABASE_DIR = os.path.abspath("database")
os.makedirs(DATABASE_DIR, exist_ok=True)

# Path do banco para uso no sistema de recovery
DATABASE_PATH = os.path.join(DATABASE_DIR, "tabela_de_dobra.db")

# Configuração do Engine do SQLAlchemy com um timeout maior
engine = create_engine(
    f'sqlite:///{os.path.join(DATABASE_DIR, "tabela_de_dobra.db")}',
    connect_args={
        "timeout": 30,
        "check_same_thread": False,
    },
    pool_pre_ping=True,
    pool_recycle=300,
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, _connection_record):
    """
    Configura o SQLite para usar modo DELETE (padrão) e desabilita funcionalidades WAL.
    Isso evita a criação de arquivos .wal e .shm.
    """
    cursor = dbapi_connection.cursor()
    try:
        # Primeiro verifica o modo atual do journal
        cursor.execute("PRAGMA journal_mode;")
        current_mode = cursor.fetchone()[0].upper()

        # Só tenta alterar para WAL se não estiver já nesse modo
        if current_mode != "WAL":
            cursor.execute("PRAGMA journal_mode=WAL;")
            logging.info(
                "Modo de jornal do SQLite alterado de %s para WAL.", current_mode
            )
        else:
            logging.info("Banco de dados já está no modo WAL.")

        # Configurações adicionais para melhorar a performance e concorrência
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA cache_size=10000;")
        cursor.execute("PRAGMA temp_store=MEMORY;")

    except (OperationalError, IntegrityError) as e:
        logging.warning(
            "Erro ao configurar pragmas do SQLite: %s. Continuando sem WAL.", e
        )
    finally:
        cursor.close()


# Cria uma "fábrica" de sessões que será usada para criar sessões individuais.
Session = sessionmaker(bind=engine)


@contextmanager
def get_session():
    """
    Fornece uma sessão transacional para uma "unidade de trabalho".
    Este context manager garante que a sessão seja sempre fechada
    corretamente, realizando commit em caso de sucesso ou rollback em caso de erro.
    Integrado com sistema de monitoramento de bloqueios.

    Uso:
        with get_session() as session:
            session.add(novo_objeto)
    """
    session = Session()
    start_time = time.time()

    try:
        yield session
        session.commit()
    except (IntegrityError, OperationalError) as e:
        session.rollback()

        # Monitora bloqueios de banco
        if "database is locked" in str(e).lower():
            duration = time.time() - start_time
            # Import local para evitar dependência circular
            from src.utils.database_recovery import (  # pylint: disable=import-outside-toplevel
                lock_monitor,
            )

            lock_monitor.record_lock_event(
                "session_operation", duration, resolved=False
            )

            logging.warning("Banco bloqueado durante sessão (duração: %.2fs)", duration)

        logging.error("Erro de banco de dados, rollback executado: %s", e)
        raise
    except Exception:
        session.rollback()
        logging.error("Erro inesperado, rollback executado.", exc_info=True)
        raise
    finally:
        session.close()


@contextmanager
def get_resilient_session(operation_name: str = "unknown"):
    """
    Versão resiliente da sessão que tenta recovery automático em caso de bloqueio.
    Usar apenas para operações críticas.

    Args:
        operation_name: Nome da operação para logging e auditoria
    """
    start_time = time.time()
    session = None
    max_attempts = 3

    for attempt in range(max_attempts):
        try:
            session = Session()
            yield session
            session.commit()
            return

        except (IntegrityError, OperationalError) as e:
            if session:
                session.rollback()
                session.close()
                session = None

            if "database is locked" in str(e).lower() and attempt < max_attempts - 1:
                duration = time.time() - start_time

                # Importa aqui para evitar circular imports
                from src.utils.database_recovery import (  # pylint: disable=import-outside-toplevel
                    DatabaseUnlocker,
                    lock_monitor,
                )

                logging.warning(
                    "Tentativa %d: Banco bloqueado em '%s'", attempt + 1, operation_name
                )
                lock_monitor.record_lock_event(operation_name, duration, resolved=False)

                # Tenta desbloqueio apenas para operações críticas
                if operation_name in [
                    "initialization",
                    "critical_read",
                    "critical_write",
                ]:
                    unlocker = DatabaseUnlocker(DATABASE_PATH)
                    if unlocker.force_unlock(create_backup=True):
                        lock_monitor.record_lock_event(
                            operation_name, duration, resolved=True
                        )
                        logging.info(
                            "Banco desbloqueado para operação: %s", operation_name
                        )
                        time.sleep(1)
                        continue

                # Se não conseguiu desbloquear, aguarda e tenta novamente
                time.sleep(2**attempt)  # Backoff exponencial
                continue

            logging.error("Erro de banco de dados em '%s': %s", operation_name, e)
            raise

        except Exception as e:
            if session:
                session.rollback()
                session.close()
            logging.error(
                "Erro inesperado em '%s': %s", operation_name, e, exc_info=True
            )
            raise

        finally:
            if session:
                session.close()


# pylint: disable=R0913,R0917


def registrar_log(session, usuario_nome, acao, tabela, registro_id, detalhes=None):
    """
    Registra uma ação no banco de dados usando a sessão fornecida.
    A sessão é gerenciada pela função que chama este log.
    """
    try:
        log = Log(
            usuario_nome=usuario_nome,
            acao=acao,
            tabela=tabela,
            registro_id=registro_id,
            detalhes=detalhes,
        )
        session.add(log)
    except (IntegrityError, OperationalError) as e:
        # O rollback será feito pelo context manager `get_session`
        logging.error("Erro de banco de dados ao criar log: %s", e)


def inicializar_banco_dados():
    """
    Cria todas as tabelas no banco de dados, se ainda não existirem.
    Se o banco estiver bloqueado após várias tentativas, pula a inicialização
    assumindo que as tabelas já existem.
    """
    max_retries = 3

    for attempt in range(max_retries):
        try:
            logging.info(
                "Inicializando o banco de dados e criando tabelas (tentativa %d/%d).",
                attempt + 1,
                max_retries,
            )
            Base.metadata.create_all(engine)
            logging.info("Banco de dados inicializado com sucesso.")
            return
        except OperationalError as e:
            if "database is locked" in str(e):
                if attempt < max_retries - 1:
                    logging.warning(
                        "Banco de dados bloqueado, tentando novamente em 1 segundo..."
                    )
                    time.sleep(1)
                    continue
                logging.warning(
                    "Banco de dados bloqueado após %d tentativas. "
                    "Pulando inicialização e assumindo que as tabelas já existem. "
                    "O aplicativo continuará normalmente.",
                    max_retries,
                )
                return  # Pula a inicialização e continua
            logging.critical("Falha ao criar tabelas no banco de dados: %s", e)
            raise
        except IntegrityError as e:
            logging.critical("Erro de banco de dados ao inicializar: %s", e)
            if attempt == max_retries - 1:
                raise
            time.sleep(1)
