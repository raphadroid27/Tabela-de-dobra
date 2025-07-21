"""
Módulo utilitário para manipulação de banco de dados no aplicativo de cálculo de dobras.
"""
import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError, OperationalError
from src.models.models import Espessura, Material, Canal, Deducao, Usuario, Log
from src.config import globals as g

# Configuração do banco de dados
DATABASE_DIR = os.path.abspath("database")
os.makedirs(DATABASE_DIR, exist_ok=True)
engine = create_engine(
    f'sqlite:///{os.path.join(DATABASE_DIR, "tabela_de_dobra.db")}')
Session = sessionmaker(bind=engine)
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
        # Lançar a exceção permite que a camada de chamada saiba que a operação falhou
        raise
    except Exception as e:
        session.rollback()
        print(f"Erro inesperado: {e}")
        raise

# Manipulação de logs


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
        # O commit será feito pela função principal que chama o registro
    except (IntegrityError, OperationalError) as e:
        print(f"Erro de banco de dados ao criar log: {e}")
