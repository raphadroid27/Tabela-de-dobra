
"""
Módulo utilitário para manipulação de banco de dados no aplicativo de cálculo de dobras.
"""
import os
from tkinter import messagebox
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError, OperationalError
from src.models.models import Espessura, Material, Canal, Deducao, Usuario, Log
from src.config import globals as g

# Configuração do banco de dados
DATABASE_DIR = os.path.abspath("database")
os.makedirs(DATABASE_DIR, exist_ok=True)
engine = create_engine(f'sqlite:///{os.path.join(DATABASE_DIR, "tabela_de_dobra.db")}')
Session = sessionmaker(bind=engine)
session = Session()

def obter_configuracoes():
    """
    Retorna um dicionário com as configurações de cada tipo de item.
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
            'valores': lambda d: (d.id,
                                d.material.nome,
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
            'item_id': Material.id,  # Corrigido de Deducao.material_id
            'valores': lambda m: (m.id, m.nome, m.densidade, m.escoamento, m.elasticidade),
            'ordem': Material.id,
            'entry': g.MAT_NOME_ENTRY,
            'busca': g.MAT_BUSCA_ENTRY,
            'campo_busca': Material.nome
        },
        'espessura': {
            'form': g.ESPES_FORM,
            'lista': g.LIST_ESP,
            'modelo': Espessura,
            'item_id': Espessura.id,  # Corrigido de Deducao.espessura_id
            'valores': lambda e: (e.id, e.valor),
            'ordem': Espessura.valor,
            'entry': g.ESP_VALOR_ENTRY,
            'busca': g.ESP_BUSCA_ENTRY,
            'campo_busca': Espessura.valor  # Corrigido de espessura.valor
        },
        'canal': {
            'form': g.CANAL_FORM,
            'lista': g.LIST_CANAL,
            'modelo': Canal,  # Corrigido de canal
            'campos': {
                'valor': g.CANAL_VALOR_ENTRY,
                'largura': g.CANAL_LARGU_ENTRY,
                'altura': g.CANAL_ALTUR_ENTRY,
                'comprimento_total': g.CANAL_COMPR_ENTRY,
                'observacao': g.CANAL_OBSER_ENTRY
            },
            'item_id': Canal.id,  # Corrigido de deducao.canal_id
            'valores': lambda c: (c.id,
                                  c.valor,
                                  c.largura,
                                  c.altura,
                                  c.comprimento_total,
                                  c.observacao),
            'ordem': Canal.valor,  # Corrigido de canal.valor
            'entry': g.CANAL_VALOR_ENTRY,
            'busca': g.CANAL_BUSCA_ENTRY,
            'campo_busca': Canal.valor  # Corrigido de canal.valor
        },
        'usuario': {
            'form': g.USUAR_FORM,
            'lista': g.LIST_USUARIO,
            'modelo': Usuario,  # Corrigido de usuario
            'valores': lambda u: (u.id, u.nome, u.role),
            'ordem': Usuario.nome,  # Corrigido de usuario.nome
            'entry': g.USUARIO_BUSCA_ENTRY,
            'campo_busca': Usuario.nome  # Corrigido de usuario.nome
        }
    }

def salvar_no_banco(obj, tipo, detalhes):
    """
    Salva um objeto no banco de dados e registra o log.
    """
    session.add(obj)
    tratativa_erro()
    registrar_log(g.USUARIO_NOME, 'adicionar', tipo, obj.id, f'{tipo} {detalhes}')

    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]

    messagebox.showinfo("Sucesso", f"Novo(a) {tipo} adicionado(a) com sucesso!",
                        parent=config['form'])

def tratativa_erro():
    """
    Trata erros de integridade e operacionais no banco de dados.
    """
    try:
        session.commit()
        print("Operação realizada com sucesso!")
    except IntegrityError as e:
        session.rollback()
        print(f"Erro de integridade no banco de dados: {e}")
    except OperationalError as e:
        session.rollback()
        print(f"Erro operacional no banco de dados: {e}")
    except Exception as e:
        session.rollback()
        print(f"Erro inesperado: {e}")
        raise

# Manipulação de logs
def registrar_log(usuario_nome, acao, tabela, registro_id, detalhes=None):
    """
    Registra uma ação no banco de dados.
    """
    log = Log(
        usuario_nome=usuario_nome,
        acao=acao,
        tabela=tabela,
        registro_id=registro_id,
        detalhes=detalhes
    )
    session.add(log)
    tratativa_erro()
