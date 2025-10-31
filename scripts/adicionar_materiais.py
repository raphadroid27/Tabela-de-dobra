"""
Script para adicionar dados de espessura, canal e dedução de múltiplos materiais
ao banco de dados.
O script conecta-se ao banco de dados SQLite, verifica se os dados já existem
e, se não existirem, os adiciona para os materiais CARBONO, H14 e INOX.
"""
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from src.models import Espessura, Material, Canal, Deducao

engine = create_engine('sqlite:///tabela_de_dobra.db')
Session = sessionmaker(bind=engine)
session = Session()


def adicionar_dados_carbono():
    """
    Adiciona os dados do material CARBONO no banco de dados.

    Cria registros de espessura, canal e dedução associados ao material CARBONO,
    caso ainda não existam no banco de dados.
    """
    dados = [
        {"espessura": 0.5, "canal": "6", "deducao": 1.2, "forca": 2.0, "obs": ""},
        {"espessura": 0.5, "canal": "10", "deducao": 1.0, "forca": None, "obs": ""},
        {"espessura": 0.8, "canal": "6", "deducao": 1.6, "forca": 7.0, "obs": ""},
        {"espessura": 0.8, "canal": "10", "deducao": 1.6, "forca": 4.0, "obs": "Canal ideal"},
        {"espessura": 1.0, "canal": "5", "deducao": 1.8, "forca": 15.0, "obs": "Máx=700"},
        {"espessura": 1.0, "canal": "6", "deducao": 1.7, "forca": 11.0, "obs": ""},
        {"espessura": 1.0, "canal": "10", "deducao": 2.0, "forca": 6.0, "obs": "Canal ideal"},
        {"espessura": 1.0, "canal": "R=28", "deducao": 0.5,
            "forca": None, "obs": "Raio peça = 34"},
        {"espessura": 1.2, "canal": "5", "deducao": 2.0, "forca": None, "obs": "Máx=700"},
        {"espessura": 1.2, "canal": "6", "deducao": 2.0, "forca": 18.0, "obs": ""},
        {"espessura": 1.2, "canal": "10", "deducao": 2.4, "forca": 9.0, "obs": "Canal ideal"},
        {"espessura": 1.5, "canal": "5", "deducao": 2.5, "forca": None, "obs": "Máx=700"},
        {"espessura": 1.5, "canal": "10", "deducao": 3.0,
            "forca": 15.0, "obs": "Canal ideal"},
        {"espessura": 2.0, "canal": "10", "deducao": 3.3, "forca": 30.0, "obs": ""},
        {"espessura": 2.0, "canal": "16", "deducao": 4.0,
            "forca": 16.0, "obs": "Canal ideal"},
        {"espessura": 2.0, "canal": "R=10", "deducao": 7.0,
            "forca": None, "obs": "Raio peça = 10"},
        {"espessura": 2.7, "canal": "10", "deducao": 4.3, "forca": None, "obs": ""},
        {"espessura": 2.7, "canal": "16", "deducao": 5.0,
            "forca": 27.0, "obs": "Canal ideal"},
        {"espessura": 2.7, "canal": "25", "deducao": 6.0, "forca": 14.0, "obs": ""},
        {"espessura": 3.2, "canal": "10", "deducao": 4.6, "forca": None, "obs": "Máx=200"},
        {"espessura": 3.2, "canal": "16", "deducao": 5.3, "forca": 43.0, "obs": ""},
        {"espessura": 3.2, "canal": "22", "deducao": 5.4, "forca": 31.0, "obs": ""},
        {"espessura": 3.2, "canal": "25", "deducao": 6.0,
            "forca": 23.0, "obs": "Canal ideal"},
        {"espessura": 3.2, "canal": "R=28", "deducao": 0.5,
            "forca": None, "obs": "Raio peça = 29"},
        {"espessura": 4.0, "canal": "16", "deducao": 6.5, "forca": None, "obs": ""},
        {"espessura": 4.0, "canal": "25", "deducao": 7.0, "forca": 44.0, "obs": ""},
        {"espessura": 4.0, "canal": "35", "deducao": 8.4,
            "forca": 32.0, "obs": "Canal ideal"},
        {"espessura": 4.3, "canal": "22", "deducao": 6.8, "forca": 60.0, "obs": ""},
        {"espessura": 4.3, "canal": "25", "deducao": 7.6, "forca": 44.0, "obs": ""},
        {"espessura": 4.3, "canal": "35", "deducao": 8.0,
            "forca": 32.0, "obs": "Canal ideal"},
        {"espessura": 4.8, "canal": "16", "deducao": 7.5, "forca": None, "obs": "Máx=200"},
        {"espessura": 4.8, "canal": "22", "deducao": 8.0, "forca": None, "obs": ""},
        {"espessura": 4.8, "canal": "25", "deducao": 8.3, "forca": 76.0, "obs": ""},
        {"espessura": 4.8, "canal": "35", "deducao": 8.5,
            "forca": 54.0, "obs": "Canal ideal"},
        {"espessura": 6.4, "canal": "25", "deducao": 10.0, "forca": None, "obs": ""},
        {"espessura": 6.4, "canal": "35", "deducao": 10.7, "forca": 85.0, "obs": ""},
        {"espessura": 6.4, "canal": "50", "deducao": 11.7,
            "forca": 45.0, "obs": "Canal ideal"},
        {"espessura": 7.9, "canal": "35", "deducao": 13.0, "forca": None, "obs": ""},
        {"espessura": 7.9, "canal": "50", "deducao": 14.0, "forca": 88.0,
         "obs": "Furo Ø8 , dist. tang. e L.D 13 , não repuxa"},
        {"espessura": 7.9, "canal": "55", "deducao": 14.5, "forca": None, "obs": ""},
        {"espessura": 7.9, "canal": "80", "deducao": 15.4,
            "forca": 46.0, "obs": "Canal ideal"},
        {"espessura": 9.5, "canal": "35", "deducao": 14.8, "forca": None, "obs": "Máx=500"},
        {"espessura": 9.5, "canal": "50", "deducao": 16.0, "forca": 151.0, "obs": ""},
        {"espessura": 9.5, "canal": "80", "deducao": 17.5,
            "forca": 79.0, "obs": "Canal ideal"},
        {"espessura": 12.7, "canal": "55", "deducao": 20.5, "forca": None, "obs": ""},
        {"espessura": 12.7, "canal": "80", "deducao": 22.5,
            "forca": 124.0, "obs": "Canal ideal"},
        {"espessura": 15.9, "canal": "80", "deducao": 28.2,
            "forca": 213.0, "obs": "Canal ideal"},
    ]

    material_obj = session.query(Material).filter_by(nome="CARBONO").first()
    if not material_obj:
        material_obj = Material(nome="CARBONO")
        session.add(material_obj)
        session.commit()

    for dado in dados:
        espessura_obj = session.query(Espessura).filter_by(
            valor=dado["espessura"]).first()
        if not espessura_obj:
            espessura_obj = Espessura(valor=dado["espessura"])
            session.add(espessura_obj)
            session.commit()

        canal_obj = session.query(Canal).filter_by(valor=dado["canal"]).first()
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
            ).first()
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
        espessura_obj = session.query(Espessura).filter_by(
            valor=dado["espessura"]).first()
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
            ).first()  # type: ignore

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


if __name__ == "__main__":
    adicionar_dados_carbono()
    adicionar_dados_h14()
    adicionar_dados_inox()
