"""
Script para adicionar dados de espessura, canal e dedução do material INOX
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

def adicionar_dados_inox():
    """
    Adiciona os dados do material INOX no banco de dados.

    Cria registros de espessura, canal e dedução associados ao material INOX,
    caso ainda não existam no banco de dados.
    """
    dados = [
        {"espessura": 0.5, "canal": "6", "deducao": 1.2, "forca": 4.0, "obs": ""},
        {"espessura": 0.8, "canal": "6", "deducao": 1.7, "forca": 12.0, "obs": ""},
        {"espessura": 1.0, "canal": "6", "deducao": 1.9, "forca": 19.0, "obs": ""},
        {"espessura": 1.0, "canal": "10", "deducao": 2.0, "forca": 10.0,
         "obs": "Falta teste"},
        {"espessura": 1.0, "canal": "R=28", "deducao": None, "forca": None,
         "obs": "Raio peça = 34mm"},
        {"espessura": 1.2, "canal": "6", "deducao": 2.2, "forca": 30.0, "obs": ""},
        {"espessura": 1.2, "canal": "10", "deducao": 2.4, "forca": 15.0,
         "obs": "Falta teste"},
        {"espessura": 1.5, "canal": "10", "deducao": 3.0, "forca": 26.0,
         "obs": "Falta teste"},
        {"espessura": 2.0, "canal": "10", "deducao": 3.3, "forca": 50.0,
         "obs": "Falta teste"},
        {"espessura": 2.0, "canal": "16", "deducao": 4.0, "forca": 26.0,
         "obs": "Falta teste"},
        {"espessura": 2.0, "canal": "50", "deducao": 7.0, "forca": None,
         "obs": "Raio peça = 8mm"},
        {"espessura": 2.5, "canal": "10", "deducao": 4.3, "forca": None,
         "obs": "MÁX=700mm"},
        {"espessura": 2.5, "canal": "16", "deducao": 4.7, "forca": 45.0, "obs": ""},
        {"espessura": 3.0, "canal": "10", "deducao": 4.9, "forca": None,
         "obs": "MÁX=200mm"},
        {"espessura": 3.0, "canal": "16", "deducao": 5.6, "forca": 71.0, "obs": ""},
        {"espessura": 3.0, "canal": "22", "deducao": 5.5, "forca": 52.0, "obs": ""},
        {"espessura": 3.0, "canal": "25", "deducao": 6.6, "forca": 38.0,
         "obs": "Raio peça = 5mm"},
        {"espessura": 3.0, "canal": "V=25; R=3", "deducao": 6.6, "forca": 38.0,
         "obs": "Raio peça = 5mm"},
        {"espessura": 3.0, "canal": "V=35; R=3", "deducao": 7.4, "forca": 27.0,
         "obs": "Raio peça = 7mm"},
        {"espessura": 4.0, "canal": "16", "deducao": 6.9, "forca": None, "obs": ""},
        {"espessura": 4.0, "canal": "25", "deducao": 7.5, "forca": 73.0, "obs": ""},
        {"espessura": 4.0, "canal": "V=35; R=3", "deducao": 8.6, "forca": 53.0,
         "obs": ""},
        {"espessura": 4.2, "canal": "22", "deducao": 7.8, "forca": 101.0, "obs": ""},
        {"espessura": 4.2, "canal": "35", "deducao": 8.8, "forca": 53.0, "obs": ""},
        {"espessura": 5.0, "canal": "16", "deducao": 8.0, "forca": None,
         "obs": "Falta teste; máximo 200mm"},
        {"espessura": 5.0, "canal": "22", "deducao": 8.3, "forca": None, "obs": ""},
        {"espessura": 5.0, "canal": "25", "deducao": 8.8, "forca": 126.0, "obs": ""},
        {"espessura": 5.0, "canal": "35", "deducao": 9.0, "forca": 90.0,
         "obs": "Canal ideal"},
        {"espessura": 5.0, "canal": "50", "deducao": 10.0, "forca": 48.0,
         "obs": "Para INOX 316 usar fator 10,4"},
        {"espessura": 5.0, "canal": "V=35; R=3", "deducao": 9.7, "forca": 90.0,
         "obs": ""},
        {"espessura": 6.0, "canal": "25", "deducao": 10.4, "forca": None, "obs": ""},
        {"espessura": 6.0, "canal": "35", "deducao": 11.2, "forca": 142.0, "obs": ""},
        {"espessura": 6.0, "canal": "50", "deducao": 12.7, "forca": 76.0, "obs": ""},
        {"espessura": 8.0, "canal": "35", "deducao": 13.3, "forca": None, "obs": ""},
        {
            "espessura": 8.0, "canal": "50", "deducao": 15.1, "forca": 147.0,
            "obs": "Furo Ø8 mm, dist. tang. e L.D 13 mm, não repuxa"
        },
        {"espessura": 9.5, "canal": "35", "deducao": 14.3, "forca": None, "obs": ""},
        {"espessura": 9.5, "canal": "50", "deducao": 16.9, "forca": 252.0,
         "obs": "MÁX=1000mm"},
        {"espessura": 10.0, "canal": "50", "deducao": 16.5, "forca": 252.0,
         "obs": "MÁX=1000mm"},
        {"espessura": 10.0, "canal": "80", "deducao": 21.1, "forca": 131.0, "obs": ""},
        {"espessura": 12.7, "canal": "50", "deducao": 20.2, "forca": None, "obs": ""},
        {"espessura": 12.7, "canal": "80", "deducao": 24.5, "forca": 207.0, "obs": ""},
        {"espessura": 16.0, "canal": "80", "deducao": 28.3, "forca": 354.0,
         "obs": "MÁX=800mm"},
    ]

    material_obj = session.query(Material).filter_by(nome="INOX").first()
    if not material_obj:
        material_obj = Material(nome="INOX")
        session.add(material_obj)
        session.commit()

    for dado in dados:
        espessura_obj = (session.query(Espessura)
                         .filter_by(valor=dado["espessura"]).first())
        if not espessura_obj:
            espessura_obj = Espessura(valor=dado["espessura"])
            session.add(espessura_obj)
            session.commit()

        canal_obj = (session.query(Canal)
                     .filter_by(valor=dado["canal"]).first())
        if not canal_obj:
            canal_obj = Canal(valor=dado["canal"])
            session.add(canal_obj)
            session.commit()

        if dado["deducao"] and dado["forca"] is not None:
            deducao_obj = session.query(Deducao).filter_by(
                espessura_id=espessura_obj.id,
                canal_id=canal_obj.id,
                material_id=material_obj.id,
                valor=dado["deducao"],
                observacao=dado["obs"],
                forca=dado["forca"]
            ).first() # type: ignore

            if not deducao_obj:
                deducao_obj = Deducao(
                    espessura_id=espessura_obj.id,
                    canal_id=canal_obj.id,
                    material_id=material_obj.id,
                    valor=dado["deducao"],
                    observacao=dado["obs"],
                    forca=dado["forca"]
                )
                session.add(deducao_obj)

    session.commit()

adicionar_dados_inox()
