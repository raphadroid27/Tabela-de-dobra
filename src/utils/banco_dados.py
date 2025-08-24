"""
Módulo utilitário para manipulação de banco de dados no aplicativo de Calculadora de Dobras.
Versão corrigida para centralizar o gerenciamento de conexões e sessões.
"""

import logging
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session as SQLAlchemySession
from sqlalchemy.orm import scoped_session, sessionmaker

from src.models.models import Base, Log, SystemControl
from src.utils.utilitarios import DB_PATH

DB_URL = f"sqlite:///{DB_PATH}"


def apply_sqlite_optimizations(dbapi_connection, _connection_record):
    """Aplica otimizações SQLite para alta concorrência após a conexão."""
    cursor = dbapi_connection.cursor()

    # Combinação de otimizações de ambos os arquivos para robustez máxima
    optimizations = [
        "PRAGMA journal_mode = WAL",  # Essencial para concorrência de leitura/escrita
        "PRAGMA synchronous = NORMAL",  # Bom balanço entre segurança e performance
        "PRAGMA busy_timeout = 60000",  # AUMENTADO para 60s para esperar por locks
        # 256MB de cache por conexão (do connection_pool.py)
        "PRAGMA cache_size = -256000",
        "PRAGMA temp_store = MEMORY",  # Temporários em memória
        # 1GB memory-mapped I/O (do connection_pool.py)
        "PRAGMA mmap_size = 1073741824",
    ]

    for pragma in optimizations:
        try:
            cursor.execute(pragma)
        except (OperationalError, IntegrityError) as e:
            logging.warning("Falha ao aplicar PRAGMA %s: %s", pragma.split(" ")[2], e)

    cursor.close()


# Configuração do Engine com pooling gerenciado pelo SQLAlchemy
engine = create_engine(
    DB_URL,
    pool_pre_ping=True,  # Verifica a conexão antes de usar
    pool_recycle=1800,  # Recicla conexões após 30 min (boa prática)
    pool_size=20,  # Tamanho do pool (do connection_pool.py)
    max_overflow=5,  # Conexões extras permitidas sob carga (do connection_pool.py)
    connect_args={
        "check_same_thread": False  # Necessário para permitir uso em múltiplas threads
    },
    echo=False,
)

# Aplicar otimizações PRAGMA em cada nova conexão criada pelo engine
event.listen(engine, "connect", apply_sqlite_optimizations)

# scoped_session garante que cada thread tenha sua própria sessão isolada
session_factory = sessionmaker(bind=engine, expire_on_commit=False)
Session = scoped_session(session_factory)


@contextmanager
def session_scope() -> Iterator[SQLAlchemySession]:
    """
    Fornece um escopo transacional seguro para threads para operações de banco de dados.
    Este é o ÚNICO método que deve ser usado para obter uma sessão.
    Ele garante que a sessão seja confirmada (commit), revertida (rollback) e fechada corretamente.
    """
    db_session = Session()
    try:
        yield db_session
        db_session.commit()
    except SQLAlchemyError as e:
        logging.error("Erro na sessão do banco de dados, revertendo: %s", e)
        db_session.rollback()
        raise
    finally:
        # Crucial: remove a sessão do escopo da thread, devolvendo a conexão ao pool.
        Session.remove()


# pylint: disable=R0913, R0917


def registrar_log(
    db_session: SQLAlchemySession,
    usuario_nome,
    acao,
    tabela,
    registro_id,
    detalhes=None,
):
    """
    Registra uma ação no banco de dados.
    Requer uma sessão ativa passada como argumento, pois não deve gerenciar a transação.
    """
    try:
        log = Log(
            usuario_nome=usuario_nome,
            acao=acao,
            tabela=tabela,
            registro_id=registro_id,
            detalhes=detalhes,
        )
        db_session.add(log)
        # O commit será feito pelo session_scope que chamou esta função.
    except (IntegrityError, OperationalError) as e:
        logging.error("Erro de banco de dados ao criar log: %s", e)


def inicializar_banco_dados():
    """Cria as tabelas do banco de dados, índices e registros iniciais, se necessário."""
    logging.info("Inicializando o banco de dados e criando tabelas.")
    Base.metadata.create_all(engine)

    _criar_indices_otimizacao()

    # Usa o session_scope para garantir que a operação seja segura
    with session_scope() as db_session:
        if not db_session.query(SystemControl).filter_by(key="UPDATE_CMD").first():
            logging.info("Inicializando o comando de atualização (UPDATE_CMD) no DB.")
            initial_command = SystemControl(
                type="COMMAND", key="UPDATE_CMD", value="NONE"
            )
            db_session.add(initial_command)


def _criar_indices_otimizacao():
    """Cria índices para otimizar consultas frequentes."""
    try:
        with engine.begin() as conn:
            indices = [
                "CREATE INDEX IF NOT EXISTS idx_deducao_material_espessura_canal "
                "ON deducao(material_id, espessura_id, canal_id)",
                "CREATE INDEX IF NOT EXISTS idx_material_nome ON material(nome)",
                "CREATE INDEX IF NOT EXISTS idx_espessura_valor ON espessura(valor)",
                "CREATE INDEX IF NOT EXISTS idx_canal_valor ON canal(valor)",
                "CREATE INDEX IF NOT EXISTS idx_log_usuario_data ON "
                "log(usuario_nome, data_hora)",
                "CREATE INDEX IF NOT EXISTS idx_system_control_type_key "
                "ON system_control(type, key)",
            ]
            for index_sql in indices:
                conn.execute(text(index_sql))
            logging.info("Índices de otimização criados/verificados com sucesso")
    except (OperationalError, IntegrityError) as e:
        logging.error("Erro ao criar índices de otimização: %s", e)
