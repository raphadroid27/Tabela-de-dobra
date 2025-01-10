import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import canal  # Certifique-se de que a classe Canal está definida em models.py

# Configuração do banco de dados
engine = create_engine('sqlite:///tabela_de_dobra.db')
Session = sessionmaker(bind=engine)
session = Session()

def adicionar_canais_ao_banco():
    with open('canais.txt', 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter='|')
        for row in reader:
            try:
                id = int(row['id'].strip())
                nome = row['nome'].strip()
                valor = row['valor'].strip()
                valor = float(valor) if valor else None
                novo_canal = canal(id=id, nome=nome, valor=valor)
                session.add(novo_canal)
            except KeyError as e:
                print(f"Chave ausente no arquivo CSV: {e}")
        session.commit()

if __name__ == "__main__":
    adicionar_canais_ao_banco()