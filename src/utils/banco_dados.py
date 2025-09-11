"""
Módulo utilitário para manipulação de banco de dados no aplicativo de Calculadora de Dobras.

Versão refatorada para usar sessões de curta duração (short-lived sessions)
e modo DELETE (padrão) para prevenir criação de arquivos WAL e SHM.
"""

import logging
import os
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import sessionmaker

from src.models.models import Base, Log

# Configuração do banco de dados
DATABASE_DIR = os.path.abspath("database")
os.makedirs(DATABASE_DIR, exist_ok=True)

# Timeout reduzido para conexões SQLAlchemy (10 segundos)
SQLALCHEMY_TIMEOUT = 10

# Configuração do Engine do SQLAlchemy
engine = create_engine(
    f'sqlite:///{os.path.join(DATABASE_DIR, "tabela_de_dobra.db")}',
    connect_args={"timeout": 30},
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, _connection_record):
    """
    Configura o SQLite para usar modo DELETE (padrão) e desabilita funcionalidades WAL.
    Isso evita a criação de arquivos .wal e .shm.
    """
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA journal_mode=DELETE;")
        cursor.execute("PRAGMA synchronous=FULL;")
        cursor.execute("PRAGMA wal_autocheckpoint=OFF;")
        logging.info(
            "Modo de jornal do SQLite definido como DELETE (WAL desabilitado)."
        )
    finally:
        cursor.close()


# Factory de sessões
Session = sessionmaker(bind=engine)


@contextmanager
def get_session():
    """Fornece uma sessão transacional para uma unidade de trabalho.

    Este context manager garante que a sessão seja sempre fechada
    corretamente, realizando commit em caso de sucesso ou rollback em caso de erro.

    Uso:
        with get_session() as session:
            session.add(novo_objeto)
    """
    session = Session()
    try:
        yield session
        session.commit()
    except (IntegrityError, OperationalError) as e:
        session.rollback()
        logging.error("Erro de banco de dados, rollback executado: %s", e)
        # Relança a exceção para que a camada superior possa tratá-la
        raise
    except Exception:
        session.rollback()
        logging.error("Erro inesperado, rollback executado.", exc_info=True)
        # Relança a exceção
        raise
    finally:
        session.close()


# pylint: disable=R0913,R0917


def registrar_log(session, usuario_nome, acao, tabela, registro_id, detalhes=None):
    """Registra uma ação no log do sistema."""
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
        logging.error("Erro ao criar log: %s", e)


def inicializar_banco_dados():
    """Cria todas as tabelas no banco de dados."""
    try:
        logging.info("Inicializando banco de dados...")
        Base.metadata.create_all(engine)
        # Limpar deduções órfãs após inicialização
        limpar_deducoes_orfas()
        logging.info("Banco de dados inicializado com sucesso")
    except OperationalError as e:
        logging.critical("Falha crítica ao inicializar banco: %s", e)
        raise


def limpar_deducoes_orfas():
    """Remove deduções órfãs (sem relacionamentos válidos) do banco de dados."""
    try:
        from src.models.models import Deducao  # pylint: disable=import-outside-toplevel

        with get_session() as session:
            deducoes = session.query(Deducao).all()
            orfaos_removidos = 0

            for d in deducoes:
                if not d.material or not d.espessura or not d.canal:
                    logging.warning(
                        "Removendo dedução órfã ID %s: material_id=%s, espessura_id=%s, canal_id=%s",  # pylint: disable=line-too-long
                        d.id,
                        d.material_id,
                        d.espessura_id,
                        d.canal_id,
                    )
                    session.delete(d)
                    orfaos_removidos += 1

            if orfaos_removidos > 0:
                session.commit()
                logging.info(
                    "Foram removidas %s deduções órfãs do banco de dados",
                    orfaos_removidos,
                )

    except (IntegrityError, OperationalError) as e:
        logging.error("Erro ao limpar deduções órfãs: %s", e)
