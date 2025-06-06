'''
Módulo utilitário para manipulação de banco de dados no aplicativo de cálculo de dobras.
'''
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

def obter_configuracoes(ui):
    '''
    Retorna um dicionário com as configurações de cada tipo de item.
    '''
    configuracoes = {}
    
    # Configuração para dedução
    if hasattr(ui, 'deducao_form'):
        configuracoes['dedução'] = {
            'form': ui.deducao_form,
            'lista': ui.deducao_lista,
            'modelo': Deducao,
            'campos': {
                'valor': ui.deducao_valor_entry,
                'observacao': ui.deducao_observacao_entry,
                'forca': ui.deducao_forca_entry
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
                'material_combo': ui.deducao_material_combo,
                'espessura_combo': ui.deducao_espessura_combo,
                'canal_combo': ui.deducao_canal_combo
            }
        }

    # Configuração para material
    if hasattr(ui, 'material_form'):
        configuracoes['material'] = {
            'form': ui.material_form,
            'lista': ui.material_lista,
            'modelo': Material,
            'campos': {
                'nome': ui.material_nome_entry,
                'densidade': ui.material_densidade_entry,
                'escoamento': ui.material_escoamento_entry,
                'elasticidade': ui.material_elasticidade_entry
            },
            'item_id': Material.id,
            'valores': lambda m: (m.id, m.nome, m.densidade, m.escoamento, m.elasticidade),
            'ordem': Material.id,
            'entry': ui.material_nome_entry,
            'busca': ui.material_busca_entry,
            'campo_busca': Material.nome
        }

    # Configuração para espessura
    if hasattr(ui, 'espessura_form'):
        configuracoes['espessura'] = {
            'form': ui.espessura_form,
            'lista': ui.espessura_lista,
            'modelo': Espessura,
            'campos': {
                'valor': ui.espessura_valor_entry
            },
            'item_id': Espessura.id,
            'valores': lambda e: (e.id, e.valor),
            'ordem': Espessura.valor,
            'entry': ui.espessura_valor_entry,
            'busca': ui.espessura_busca_entry,
            'campo_busca': Espessura.valor
        }

    # Configuração para canal
    if hasattr(ui, 'canal_form'):
        configuracoes['canal'] = {
            'form': ui.canal_form,
            'lista': ui.canal_lista,
            'modelo': Canal,
            'campos': {
                'valor': ui.canal_valor_entry,
                'largura': ui.canal_largura_entry,
                'altura': ui.canal_altura_entry,
                'comprimento_total': ui.canal_comprimento_entry,
                'observacao': ui.canal_observacao_entry
            },
            'item_id': Canal.id,
            'valores': lambda c: (c.id,
                                  c.valor,
                                  c.largura,
                                  c.altura,
                                  c.comprimento_total,
                                  c.observacao),
            'ordem': Canal.valor,
            'busca': ui.canal_busca_entry,
            'campo_busca': Canal.valor
        }

    # Configuração para usuário
    if hasattr(ui, 'usuario_form'):
        configuracoes['usuario'] = {
            'form': ui.usuario_form,
            'lista': ui.usuario_lista,
            'modelo': Usuario,
            'campos': {
                'nome': ui.usuario_nome_entry,
                'role': ui.usuario_role_combo  # Assumindo que existe um combo para role
            },
            'item_id': Usuario.id,
            'valores': lambda u: (u.id, u.nome, u.role),
            'ordem': Usuario.nome,
            'entry': ui.usuario_busca_entry,
            'campo_busca': Usuario.nome
        }
    
    return configuracoes

def salvar_no_banco(obj, tipo, detalhes, ui):
    '''
    Salva um objeto no banco de dados e registra o log.
    '''
    session.add(obj)
    tratativa_erro()
    registrar_log(g.USUARIO_NOME, 'adicionar', tipo, obj.id, f'{tipo} {detalhes}')

    configuracoes = obter_configuracoes(ui)
    config = configuracoes[tipo]

    messagebox.showinfo("Sucesso", f"Novo(a) {tipo} adicionado(a) com sucesso!",
                        parent=config['form'])

def tratativa_erro():
    '''
    Trata erros de integridade e operacionais no banco de dados.
    '''
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
    '''
    Registra uma ação no banco de dados.
    '''
    log = Log(
        usuario_nome=usuario_nome,
        acao=acao,
        tabela=tabela,
        registro_id=registro_id,
        detalhes=detalhes
    )
    session.add(log)
    tratativa_erro()
