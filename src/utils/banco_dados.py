"""
Módulo utilitário para manipulação de banco de dados no aplicativo de Calculadora de Dobras.
Versão corrigida para centralizar o gerenciamento de conexões e sessões.
"""

import logging
import os  # Importa o módulo 'os' para interagir com o sistema de arquivos

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import sessionmaker

from src.models.models import Base, Log

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


def inicializar_banco_dados():
    """Cria as tabelas do banco de dados, se necessário."""
    logging.info("Inicializando o banco de dados e criando tabelas.")
    Base.metadata.create_all(engine)

    # Lógica de inicialização de SystemControl para comandos foi removida
    # pois agora é gerenciada por arquivos.
