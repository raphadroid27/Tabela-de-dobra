import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, espessura, canal, deducao

# Configuração do banco de dados
engine = create_engine('sqlite:///tabela_de_dobra.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Função para ler o arquivo espessuras.txt e inserir os dados no banco de dados
def insert_espessuras(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter='|')
        next(reader)  # Pular o cabeçalho
        next(reader)  # Pular a linha de separadores
        for row in reader:
            if len(row) == 3:
                id_str, nome, valor_str = row
                valor = float(valor_str.strip())
                # Verificar se a espessura já existe
                existing_espessura = session.query(espessura).filter_by(nome=nome.strip(), valor=valor).first()
                if not existing_espessura:
                    nova_espessura = espessura(nome=nome.strip(), valor=valor)
                    session.add(nova_espessura)
        session.commit()

# Função para ler o arquivo canais.txt e inserir os dados no banco de dados
def insert_canais(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter='|')
        next(reader)  # Pular o cabeçalho
        next(reader)  # Pular a linha de separadores
        for row in reader:
            if len(row) == 3:
                id_str, nome, valor_str = row
                valor = float(valor_str.strip()) if valor_str.strip() else None
                # Verificar se o canal já existe
                existing_canal = session.query(canal).filter_by(nome=nome.strip(), valor=valor).first()
                if not existing_canal:
                    novo_canal = canal(nome=nome.strip(), valor=valor)
                    session.add(novo_canal)
        session.commit()

# Função para ler o arquivo carbono.txt e inserir os dados no banco de dados
def insert_deducoes(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter='|')
        next(reader)  # Pular o cabeçalho
        for row in reader:
            if len(row) == 3:
                esp_nome, canal_nome, valor_str = row
                valor_str = valor_str.strip().replace(',', '.')
                if valor_str.replace('.', '', 1).isdigit():
                    valor = float(valor_str)
                    
                    # Obter espessura e canal correspondentes
                    esp = session.query(espessura).filter_by(nome=esp_nome.strip()).first()
                    can = session.query(canal).filter_by(nome=canal_nome.strip()).first()
                    
                    if esp and can:
                        # Verificar se a dedução já existe
                        existing_deducao = session.query(deducao).filter_by(espessura_id=esp.id, canal_id=can.id, valor=valor).first()
                        if not existing_deducao:
                            deducao_instance = deducao(espessura_id=esp.id, canal_id=can.id, valor=valor)
                            session.add(deducao_instance)
        session.commit()

# Caminhos dos arquivos
espessuras_file_path = 'c:/Users/Luma/Github/Tabela-de-dobra/espessuras.txt'
canais_file_path = 'c:/Users/Luma/Github/Tabela-de-dobra/canais.txt'
carbono_file_path = 'c:/Users/Luma/Github/Tabela-de-dobra/carbono.txt'

# Inserir dados nos bancos de dados
insert_espessuras(espessuras_file_path)
insert_canais(canais_file_path)
insert_deducoes(carbono_file_path)