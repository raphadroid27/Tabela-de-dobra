import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import espessura, material, canal, deducao

# Configuração do banco de dados
engine = create_engine('sqlite:///tabela_de_dobra.db')
Session = sessionmaker(bind=engine)
session = Session()

def inserir_dados_inox():
    material_nome = "INOX"
    material_obj = session.query(material).filter_by(nome=material_nome).first()
    if not material_obj:
        material_obj = material(nome=material_nome)
        session.add(material_obj)
        session.commit()

    dados = [
        {"esp": "0,5mm", "canal": "6", "deducao": "1,2", "forca": "4 ton/m", "obs": ""},
        {"esp": "0,8mm", "canal": "6", "deducao": "1,7", "forca": "12 ton/m", "obs": ""},
        {"esp": "1,0mm", "canal": "6", "deducao": "1,9", "forca": "19 ton/m", "obs": ""},
        {"esp": "1,0mm", "canal": "10", "deducao": "2,0", "forca": "10 ton/m", "obs": "Falta teste"},
        {"esp": "1,0mm", "canal": "R=28", "deducao": "", "forca": "Sem correspondência", "obs": "Raio peça = 34mm"},
        {"esp": "1,2mm", "canal": "6", "deducao": "2,2", "forca": "30 ton/m", "obs": ""},
        {"esp": "1,2mm", "canal": "10", "deducao": "2,4", "forca": "15 ton/m", "obs": "Falta teste"},
        {"esp": "1,5mm", "canal": "10", "deducao": "3,0", "forca": "26 ton/m", "obs": "Falta teste"},
        {"esp": "2,0mm", "canal": "10", "deducao": "3,3", "forca": "50 ton/m", "obs": "Falta teste"},
        {"esp": "2,0mm", "canal": "16", "deducao": "4,0", "forca": "26 ton/m", "obs": "Falta teste"},
        {"esp": "2,0mm", "canal": "50", "deducao": "7,0", "forca": "Sem correspondência", "obs": "Raio peça = 8mm"},
        {"esp": "2,5mm", "canal": "10", "deducao": "4,3", "forca": "Sem correspondência", "obs": "MÁX=700mm"},
        {"esp": "2,5mm", "canal": "16", "deducao": "4,7", "forca": "45 ton/m", "obs": ""},
        {"esp": "3,0mm", "canal": "10", "deducao": "4,9", "forca": "Sem correspondência", "obs": "MÁX=200mm"},
        {"esp": "3,0mm", "canal": "16", "deducao": "5,6", "forca": "71 ton/m", "obs": ""},
        {"esp": "3,0mm", "canal": "22", "deducao": "5,5", "forca": "52 ton/m", "obs": ""},
        {"esp": "3,0mm", "canal": "25", "deducao": "6,6", "forca": "38 ton/m", "obs": "Raio peça = 5mm"},
        {"esp": "3,0mm", "canal": "V=25; R=3", "deducao": "6,6", "forca": "38 ton/m", "obs": "Raio peça = 5mm"},
        {"esp": "3,0mm", "canal": "V=35; R=3", "deducao": "7,4", "forca": "27 ton/m", "obs": "Raio peça = 7mm"},
        {"esp": "4,0mm", "canal": "16", "deducao": "6,9", "forca": "Sem correspondência", "obs": ""},
        {"esp": "4,0mm", "canal": "25", "deducao": "7,5", "forca": "73 ton/m", "obs": ""},
        {"esp": "4,0mm", "canal": "V=35; R=3", "deducao": "8,6", "forca": "53 ton/m", "obs": ""},
        {"esp": "4,2mm", "canal": "22", "deducao": "7,8", "forca": "101 ton/m", "obs": ""},
        {"esp": "4,2mm", "canal": "35", "deducao": "8,8", "forca": "53 ton/m", "obs": ""},
        {"esp": "5,0mm", "canal": "16", "deducao": "8,0", "forca": "Sem correspondência", "obs": "Falta teste; máximo 200mm"},
        {"esp": "5,0mm", "canal": "22", "deducao": "8,3", "forca": "Sem correspondência", "obs": ""},
        {"esp": "5,0mm", "canal": "25", "deducao": "8,8", "forca": "126 ton/m", "obs": ""},
        {"esp": "5,0mm", "canal": "35", "deducao": "9,0", "forca": "90 ton/m", "obs": "Canal ideal"},
        {"esp": "5,0mm", "canal": "50", "deducao": "10,0", "forca": "48 ton/m", "obs": "Para INOX 316 usar fator 10,4"},
        {"esp": "5,0mm", "canal": "V=35; R=3", "deducao": "9,7", "forca": "90 ton/m", "obs": ""},
        {"esp": "6,0mm", "canal": "25", "deducao": "10,4", "forca": "Sem correspondência", "obs": ""},
        {"esp": "6,0mm", "canal": "35", "deducao": "11,2", "forca": "142 ton/m", "obs": ""},
        {"esp": "6,0mm", "canal": "50", "deducao": "12,7", "forca": "76 ton/m", "obs": ""},
        {"esp": "8,0mm", "canal": "35", "deducao": "13,3", "forca": "Sem correspondência", "obs": ""},
        {"esp": "8,0mm", "canal": "50", "deducao": "15,1", "forca": "147 ton/m", "obs": "Furo Ø8 mm, dist. tang. e L.D 13 mm, não repuxa"},
        {"esp": "9,5mm", "canal": "35", "deducao": "14,3", "forca": "Sem correspondência", "obs": ""},
        {"esp": "9,5mm", "canal": "50", "deducao": "16,9", "forca": "252 ton/m", "obs": "MÁX=1000mm"},
        {"esp": "10,0mm", "canal": "50", "deducao": "16,5", "forca": "252 ton/m", "obs": "MÁX=1000mm"},
        {"esp": "10,0mm", "canal": "80", "deducao": "21,1", "forca": "131 ton/m", "obs": ""},
        {"esp": "12,7mm", "canal": "50", "deducao": "20,2", "forca": "Sem correspondência", "obs": ""},
        {"esp": "12,7mm", "canal": "80", "deducao": "24,5", "forca": "207 ton/m", "obs": ""},
        {"esp": "16,0mm", "canal": "80", "deducao": "28,3", "forca": "354 ton/m", "obs": "MÁX=800mm"}
    ]

    for dado in dados:
        espessura_valor = float(dado["esp"].replace("mm", "").replace(",", "."))
        canal_valor = dado["canal"]
        deducao_valor = float(dado["deducao"].replace(",", ".")) if dado["deducao"] else None
        forca_valor = None
        if "ton/m" in dado["forca"]:
            forca_valor = float(dado["forca"].replace(" ton/m", ""))

        espessura_obj = session.query(espessura).filter_by(valor=espessura_valor).first()
        if not espessura_obj:
            espessura_obj = espessura(valor=espessura_valor)
            session.add(espessura_obj)
            session.commit()

        canal_obj = session.query(canal).filter_by(valor=canal_valor).first()
        if not canal_obj:
            canal_obj = canal(valor=canal_valor)
            session.add(canal_obj)
            session.commit()

        deducao_obj = session.query(deducao).filter_by(
            espessura_id=espessura_obj.id,
            canal_id=canal_obj.id,
            material_id=material_obj.id
        ).first()

        if not deducao_obj:
            nova_deducao = deducao(
                espessura_id=espessura_obj.id,
                canal_id=canal_obj.id,
                material_id=material_obj.id,
                valor=deducao_valor,
                forca=forca_valor,
                observacao=dado["obs"]
            )
            session.add(nova_deducao)

    session.commit()

if __name__ == "__main__":
    inserir_dados_inox()