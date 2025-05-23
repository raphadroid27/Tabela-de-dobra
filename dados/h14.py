"""
Script para adicionar dados de espessura, canal e dedução do material H14
ao banco de dados.
O script conecta-se ao banco de dados SQLite, verifica se os dados já existem
e, se não existirem, os adiciona.
"""
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from src.models import Espessura, Material, Canal, Deducao

engine = create_engine('sqlite:///tabela_de_dobra.db')
Session = sessionmaker(bind=engine)
session = Session()

def adicionar_dados_h14():
    """
    Adiciona os dados do material H14 no banco de dados.

    Cria registros de espessura, canal e dedução associados ao material H14,
    caso ainda não existam no banco de dados.
    """
    dados = [
        {"espessura": 1.0, "canal": "10", "deducao": 1.7, "obs": ""},
        {"espessura": 1.5, "canal": "10", "deducao": 3.2, "obs": "R=0,8"},
        {"espessura": 2.0, "canal": "16", "deducao": 3.3, "obs": "Falta teste"},
        {"espessura": 2.5, "canal": "16", "deducao": 4.0, "obs": "Não usar em chapa xadrez"},
        {"espessura": 2.5, "canal": "25", "deducao": 4.1, "obs": ""},
        {"espessura": 3.0, "canal": "16", "deducao": 4.7, "obs": "Não usar em chapa xadrez"},
        {"espessura": 4.0, "canal": "16", "deducao": 6.5, "obs": "Não usar em chapa xadrez"},
        {"espessura": 4.0, "canal": "25", "deducao": 6.7, "obs": ""},
        {"espessura": 4.0, "canal": "35", "deducao": 6.6, "obs": ""},
        {"espessura": 6.0, "canal": "35", "deducao": 10.6, "obs": ""},
        {"espessura": 8.0, "canal": "35", "deducao": 12.8, "obs": "R=0,8"},
        {"espessura": 8.0, "canal": "50", "deducao": 13.5, "obs": ""},
        {"espessura": 10.0, "canal": "35", "deducao": 14.8, "obs": ""},
        {"espessura": 10.0, "canal": "V=35; R=3", "deducao": 15.1, "obs": ""},
        {"espessura": 10.0, "canal": "50", "deducao": 16.0, "obs": ""},
        {"espessura": 10.0, "canal": "80", "deducao": 17.5, "obs": ""},
    ]

    material_obj = session.query(Material).filter_by(nome="H14").first()
    if not material_obj:
        material_obj = Material(nome="H14")
        session.add(material_obj)
        session.commit()

    for dado in dados:
        espessura_obj = session.query(Espessura).filter_by(valor=dado["espessura"]).first()
        if not espessura_obj:
            espessura_obj = Espessura(valor=dado["espessura"])
            session.add(espessura_obj)
            session.commit()

        canal_obj = session.query(Canal).filter_by(valor=dado["canal"]).first()
        if not canal_obj:
            canal_obj = Canal(valor=dado["canal"])
            session.add(canal_obj)
            session.commit()

        deducao_obj = session.query(Deducao).filter_by(
            espessura_id=espessura_obj.id,
            canal_id=canal_obj.id,
            material_id=material_obj.id,
            valor=dado["deducao"],
            observacao=dado["obs"]
        ).first()
        if not deducao_obj:
            deducao_obj = Deducao(
                espessura_id=espessura_obj.id,
                canal_id=canal_obj.id,
                material_id=material_obj.id,
                valor=dado["deducao"],
                observacao=dado["obs"]
            )
            session.add(deducao_obj)

    session.commit()

adicionar_dados_h14()
