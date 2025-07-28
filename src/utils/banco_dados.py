"""
Módulo utilitário para manipulação de banco de dados no aplicativo de cálculo de dobras.
"""
import os
import logging
from contextlib import contextmanager
from typing import Tuple, Optional, Type, Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# FIX 1: Importar o TIPO Session com um alias para evitar conflito de nome
from sqlalchemy.orm import Session as SQLAlchemySession
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

from src.models.models import (
    Espessura, Material, Canal, Deducao, Usuario, Log, SystemControl, Base)
from src.config import globals as g
from src.utils.utilitarios import DB_PATH


# Configuração do banco de dados (executada uma vez na importação)
DATABASE_DIR = os.path.abspath("database")
os.makedirs(DATABASE_DIR, exist_ok=True)
engine = create_engine(
    f'sqlite:///{os.path.join(DATABASE_DIR, "tabela_de_dobra.db")}')

# 'Session' (com 'S' maiúsculo) é a FÁBRICA de sessões.
Session = sessionmaker(bind=engine)

# 'session' (com 's' minúsculo) é uma instância de sessão global para uso simples.
session = Session()


def obter_configuracoes():
    """
    Retorna um dicionário com as configurações de cada tipo de item.
    Esta função mapeia os tipos de dados para os widgets da UI correspondentes,
    sendo essencial para a camada de handlers.
    """
    return {
        'principal': {
            'form': g.PRINC_FORM,
        },
        'dedução': {
            'form': g.DEDUC_FORM,
            'lista': g.LIST_DED,
            'modelo': Deducao,
            'campos': {
                'valor': g.DED_VALOR_ENTRY,
                'observacao': g.DED_OBSER_ENTRY,
                'forca': g.DED_FORCA_ENTRY
            },
            'item_id': Deducao.id,
            'valores': lambda d: (d.material.nome,
                                  d.espessura.valor,
                                  d.canal.valor,
                                  d.valor,
                                  d.observacao,
                                  d.forca),
            'ordem': Deducao.valor,
            'entries': {
                'material_combo': g.DED_MATER_COMB,
                'espessura_combo': g.DED_ESPES_COMB,
                'canal_combo': g.DED_CANAL_COMB
            }
        },
        'material': {
            'form': g.MATER_FORM,
            'lista': g.LIST_MAT,
            'modelo': Material,
            'campos': {
                'nome': g.MAT_NOME_ENTRY,
                'densidade': g.MAT_DENS_ENTRY,
                'escoamento': g.MAT_ESCO_ENTRY,
                'elasticidade': g.MAT_ELAS_ENTRY
            },
            'item_id': Material.id,
            'valores': lambda m: (m.nome, m.densidade, m.escoamento, m.elasticidade),
            'ordem': Material.id,
            'entry': g.MAT_NOME_ENTRY,
            'busca': g.MAT_BUSCA_ENTRY,
            'campo_busca': Material.nome
        },
        'espessura': {
            'form': g.ESPES_FORM,
            'lista': g.LIST_ESP,
            'modelo': Espessura,
            'campos': {
                'valor': g.ESP_VALOR_ENTRY
            },
            'item_id': Espessura.id,
            'valores': lambda e: (e.valor,),
            'ordem': Espessura.valor,
            'entry': g.ESP_VALOR_ENTRY,
            'busca': g.ESP_BUSCA_ENTRY,
            'campo_busca': Espessura.valor
        },
        'canal': {
            'form': g.CANAL_FORM,
            'lista': g.LIST_CANAL,
            'modelo': Canal,
            'campos': {
                'valor': g.CANAL_VALOR_ENTRY,
                'largura': g.CANAL_LARGU_ENTRY,
                'altura': g.CANAL_ALTUR_ENTRY,
                'comprimento_total': g.CANAL_COMPR_ENTRY,
                'observacao': g.CANAL_OBSER_ENTRY
            },
            'item_id': Canal.id,
            'valores': lambda c: (c.valor,
                                  c.largura,
                                  c.altura,
                                  c.comprimento_total,
                                  c.observacao),
            'ordem': Canal.valor,
            'entry': g.CANAL_VALOR_ENTRY,
            'busca': g.CANAL_BUSCA_ENTRY,
            'campo_busca': Canal.valor
        },
        'usuario': {
            'form': g.USUAR_FORM,
            'lista': g.LIST_USUARIO,
            'modelo': Usuario,
            'valores': lambda u: (u.id, u.nome, u.role),
            'ordem': Usuario.nome,
            'busca': g.USUARIO_BUSCA_ENTRY,
            'campo_busca': Usuario.nome
        }
    }


def tratativa_erro():
    """
    Realiza o commit da sessão e trata erros de integridade e operacionais.
    """
    try:
        session.commit()
    except (IntegrityError, OperationalError) as e:
        session.rollback()
        print(f"Erro de banco de dados: {e}")
        raise
    except Exception as e:
        session.rollback()
        print(f"Erro inesperado: {e}")
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
            detalhes=detalhes
        )
        session.add(log)
    except (IntegrityError, OperationalError) as e:
        print(f"Erro de banco de dados ao criar log: {e}")


@contextmanager
# FIX 2: Usar o alias 'SQLAlchemySession' na anotação de tipo do retorno
def session_scope() -> Iterator[Tuple[Optional[SQLAlchemySession], Optional[Type[SystemControl]]]]:
    """
    Fornece um escopo transacional para operações de banco de dados.
    """
    if not os.path.exists(DB_PATH):
        logging.error("Banco de dados não encontrado em: %s", DB_PATH)
        yield None, None
        return

    # FIX 3: Usar o alias 'SQLAlchemySession' na anotação da variável local
    db_session: Optional[SQLAlchemySession] = None
    try:
        # Usa a fábrica de sessão 'Session' (com 'S' maiúsculo) já configurada
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

    # Cria uma sessão local para esta operação específica
    db_session = Session()
    try:
        if not db_session.query(SystemControl).filter_by(key='UPDATE_CMD').first():
            logging.info(
                "Inicializando o comando de atualização (UPDATE_CMD) no DB.")
            initial_command = SystemControl(
                type='COMMAND', key='UPDATE_CMD', value='NONE')
            db_session.add(initial_command)
            db_session.commit()
    finally:
        db_session.close()
