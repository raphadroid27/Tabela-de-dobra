"""
Módulo utilitário para manipulação de banco de dados no aplicativo de Calculadora de Dobras.
Versão corrigida para centralizar o gerenciamento de conexões e sessões.
"""

import logging
import os
from contextlib import contextmanager
from typing import Iterator, Optional, Tuple, Type

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session as SQLAlchemySession
from sqlalchemy.orm import sessionmaker

from src.models.models import Base, Log, SystemControl
from src.utils.utilitarios import DB_PATH

DATABASE_DIR = os.path.abspath("database")
os.makedirs(DATABASE_DIR, exist_ok=True)
engine = create_engine(f'sqlite:///{os.path.join(DATABASE_DIR, "tabela_de_dobra.db")}')

Session = sessionmaker(bind=engine)
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
    """Cria as tabelas do banco de dados e registros iniciais, se necessário."""
    logging.info("Inicializando o banco de dados e criando tabelas.")
    Base.metadata.create_all(engine)

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
