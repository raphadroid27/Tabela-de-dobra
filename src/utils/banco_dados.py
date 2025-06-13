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


def obter_configuracoes(form_ui):
    """
    Retorna um dicionário com as configurações de cada tipo de item.
    """
    configuracoes = {}

    # Configuração para dedução
    if hasattr(form_ui, "deducao_form"):
        configuracoes["dedução"] = {
            "form": form_ui.deducao_form,
            "lista": form_ui.deducao_lista,
            "modelo": Deducao,
            "campos": {
                "valor": form_ui.deducao_valor_entry,
                "observacao": form_ui.deducao_observacao_entry,
                "forca": form_ui.deducao_forca_entry,
            },
            "item_id": Deducao.id,
            "valores": lambda d: (
                d.id,
                d.material.nome,
                d.espessura.valor,
                d.canal.valor,
                d.valor,
                d.observacao,
                d.forca,
            ),
            "ordem": Deducao.valor,
            "entries": {
                "material_combo": form_ui.deducao_material_combo,
                "espessura_combo": form_ui.deducao_espessura_combo,
                "canal_combo": form_ui.deducao_canal_combo,
            },
        }

    # Configuração para material
    if hasattr(form_ui, "material_form"):
        configuracoes["material"] = {
            "form": form_ui.material_form,
            "lista": form_ui.material_lista,
            "modelo": Material,
            "campos": {
                "nome": form_ui.material_nome_entry,
                "densidade": form_ui.material_densidade_entry,
                "escoamento": form_ui.material_escoamento_entry,
                "elasticidade": form_ui.material_elasticidade_entry,
            },
            "item_id": Material.id,
            "valores": lambda m: (m.id, m.nome, m.densidade, m.escoamento, m.elasticidade),
            "ordem": Material.id,
            "entry": form_ui.material_nome_entry,
            "busca": form_ui.material_busca_entry,
            "campo_busca": Material.nome,
        }

    # Configuração para espessura
    if hasattr(form_ui, "espessura_form"):
        configuracoes["espessura"] = {
            "form": form_ui.espessura_form,
            "lista": form_ui.espessura_lista,
            "modelo": Espessura,
            "campos": {"valor": form_ui.espessura_valor_entry},
            "item_id": Espessura.id,
            "valores": lambda e: (e.id, e.valor),
            "ordem": Espessura.valor,
            "entry": form_ui.espessura_valor_entry,
            "busca": form_ui.espessura_busca_entry,
            "campo_busca": Espessura.valor,
        }

    # Configuração para canal
    if hasattr(form_ui, "canal_form"):
        configuracoes["canal"] = {
            "form": form_ui.canal_form,
            "lista": form_ui.canal_lista,
            "modelo": Canal,
            "campos": {
                "valor": form_ui.canal_valor_entry,
                "largura": form_ui.canal_largura_entry,
                "altura": form_ui.canal_altura_entry,
                "comprimento_total": form_ui.canal_comprimento_entry,
                "observacao": form_ui.canal_observacao_entry,
            },
            "item_id": Canal.id,
            "valores": lambda c: (
                c.id,
                c.valor,
                c.largura,
                c.altura,
                c.comprimento_total,
                c.observacao,
            ),
            "ordem": Canal.valor,
            "busca": form_ui.canal_busca_entry,
            "campo_busca": Canal.valor,
        }

    # Configuração para usuário
    if hasattr(form_ui, "usuario_form"):
        configuracoes["usuario"] = {
            "form": form_ui.usuario_form,
            "lista": form_ui.usuario_lista,
            "modelo": Usuario,
            "valores": lambda u: (u.id, u.nome, u.role),
            "ordem": Usuario.nome,
            "entry": form_ui.usuario_busca_entry,
            "campo_busca": Usuario.nome,
        }

    return configuracoes


def salvar_no_banco(obj, tipo, detalhes, ui):
    """
    Salva um objeto no banco de dados e registra o log.
    Invalida cache após modificação.
    """
    from src.utils.cache import cache_manager

    session.add(obj)
    tratativa_erro()
    registrar_log(g.USUARIO_NOME, "adicionar", tipo, obj.id, f"{tipo} {detalhes}")

    # Invalidar cache relevante
    cache_manager.invalidate_cache()

    configuracoes = obter_configuracoes(ui)
    config = configuracoes[tipo]

    messagebox.showinfo(
        "Sucesso", f"Novo(a) {tipo} adicionado(a) com sucesso!", parent=config["form"]
    )


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
        detalhes=detalhes,
    )
    session.add(log)
    tratativa_erro()
