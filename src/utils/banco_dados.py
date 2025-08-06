"""
Módulo utilitário para manipulação de banco de dados no aplicativo de cálculo de dobras.
"""

import logging
import os
from contextlib import contextmanager
from typing import Iterator, Optional, Tuple, Type

from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session as SQLAlchemySession
from sqlalchemy.orm import sessionmaker

from src.models.models import Base, Log, SystemControl
from src.utils.utilitarios import DB_PATH

DATABASE_DIR = os.path.abspath("database")
os.makedirs(DATABASE_DIR, exist_ok=True)

# Configurações otimizadas para SQLite em rede
DB_URL = f'sqlite:///{os.path.join(DATABASE_DIR, "tabela_de_dobra.db")}'


def apply_sqlite_optimizations(dbapi_connection, _connection_record):
    """Aplica otimizações SQLite após a conexão."""
    cursor = dbapi_connection.cursor()

    # Configurações para melhor performance em rede
    optimizations = [
        "PRAGMA journal_mode = WAL",  # Write-Ahead Logging
        "PRAGMA synchronous = NORMAL",  # Balanceia performance e segurança
        "PRAGMA cache_size = -64000",  # 64MB de cache
        "PRAGMA temp_store = MEMORY",  # Temporários em memória
        "PRAGMA mmap_size = 268435456",  # 256MB memory-mapped I/O
        "PRAGMA busy_timeout = 30000",  # 30s timeout para locks
        "PRAGMA wal_autocheckpoint = 1000",  # Checkpoint automático
    ]

    for pragma in optimizations:
        try:
            cursor.execute(pragma)
        except (OperationalError, IntegrityError) as e:
            logging.warning("Falha ao aplicar %s: %s", pragma, e)

    cursor.close()


engine = create_engine(
    DB_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={
        "timeout": 30,
        "check_same_thread": False,
    },
    echo=False,  # Disable SQL logging em produção
)

# Aplicar otimizações após cada conexão
event.listen(engine, "connect", apply_sqlite_optimizations)

Session = sessionmaker(bind=engine, expire_on_commit=False)
session = Session()


def tratativa_erro():
    """
    Realiza o commit da sessão e trata erros de integridade e operacionais.
    """
    try:
        session.commit()
    except (IntegrityError, OperationalError) as e:
        session.rollback()
        logging.error("Erro de banco de dados: %s", e)
        raise
    except Exception as e:
        session.rollback()
        logging.error("Erro inesperado: %s", e)
        raise


def registrar_log(usuario_nome, acao, tabela, registro_id, detalhes=None):
    """
    Registra uma ação no banco de dados.
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
        logging.error("Erro de banco de dados ao criar log: %s", e)


@contextmanager
def session_scope() -> (
    Iterator[Tuple[Optional[SQLAlchemySession], Optional[Type[SystemControl]]]]
):
    """Fornece um escopo transacional para operações de banco de dados."""
    if not os.path.exists(DB_PATH):
        logging.error("Banco de dados não encontrado em: %s", DB_PATH)
        yield None, None
        return

    db_session: Optional[SQLAlchemySession] = None
    try:
        db_session = Session()
        yield db_session, SystemControl
        db_session.commit()
    except SQLAlchemyError as e:
        logging.error("Erro na sessão do banco de dados: %s", e)
        if db_session:
            db_session.rollback()
        raise
    finally:
        if db_session:
            db_session.close()


def inicializar_banco_dados():
    """Cria as tabelas do banco de dados, índices e registros iniciais, se necessário."""
    logging.info("Inicializando o banco de dados e criando tabelas.")
    Base.metadata.create_all(engine)

    # Criar índices para otimizar consultas frequentes
    _criar_indices_otimizacao()

    db_session = Session()
    try:
        if not db_session.query(SystemControl).filter_by(key="UPDATE_CMD").first():
            logging.info("Inicializando o comando de atualização (UPDATE_CMD) no DB.")
            initial_command = SystemControl(
                type="COMMAND", key="UPDATE_CMD", value="NONE"
            )
            db_session.add(initial_command)
            db_session.commit()
    finally:
        db_session.close()


def _criar_indices_otimizacao():
    """Cria índices para otimizar consultas frequentes."""
    try:
        with engine.connect() as conn:

            # Índices para a tabela de deduções (consulta mais frequente)
            conn.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_deducao_material_espessura_canal 
                ON deducao(material_id, espessura_id, canal_id)
                """
                )
            )

            # Índices para busca por valores específicos
            conn.execute(
                text("CREATE INDEX IF NOT EXISTS idx_material_nome ON material(nome)")
            )

            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_espessura_valor ON espessura(valor)"
                )
            )

            conn.execute(
                text("CREATE INDEX IF NOT EXISTS idx_canal_valor ON canal(valor)")
            )

            # Índice para logs (se precisar consultar histórico)
            conn.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_log_usuario_data 
                ON log(usuario_nome, data_hora)
                """
                )
            )

            # Índice para system_control
            conn.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_system_control_type_key 
                ON system_control(type, key)
                """
                )
            )

            conn.commit()
            logging.info("Índices de otimização criados com sucesso")

    except (OperationalError, IntegrityError) as e:
        logging.error("Erro ao criar índices de otimização: %s", e)
