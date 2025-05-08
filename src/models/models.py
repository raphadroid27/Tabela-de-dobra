'''
Modelo de dados para o sistema de cálculo de dobra de chapas. Este módulo define as classes que 
representam as tabelas do banco de dados, utilizando SQLAlchemy para ORM.
As classes definem os atributos e relacionamentos entre as tabelas, permitindo a manipulação dos 
dados de forma orientada a objetos. As tabelas incluem informações sobre usuários, espessuras, 
materiais, canais, deduções e logs de ações realizadas no sistema.
'''
import os
from datetime import datetime
from os import path, makedirs
from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey, DateTime, create_engine, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

class Usuario(Base):
    """
    Representa a tabela de usuários no banco de dados.
    Contém informações sobre o nome, senha e o papel do usuário no sistema.
    """
    __tablename__ = 'usuario'
    id = Column(Integer, primary_key=True)
    nome = Column(String, unique=True, nullable=False)
    senha = Column(String, nullable=False)
    role = Column(String, default="viewer")

class Espessura(Base):
    """
    Representa a tabela de espessuras no banco de dados.
    Contém o valor da espessura em milímetros.
    """
    __tablename__ = 'espessura'
    id = Column(Integer, primary_key=True, autoincrement=True)
    valor = Column(Float, nullable=False)

class Material(Base):  # Ajustado para PascalCase
    """
    Representa a tabela de materiais no banco de dados.
    Contém informações como nome, densidade, limite de escoamento e módulo de elasticidade.
    """
    __tablename__ = 'material'
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    densidade = Column(Float)
    escoamento = Column(Float)
    elasticidade = Column(Float)

class Canal(Base):  # Ajustado para PascalCase
    """
    Representa a tabela de canais no banco de dados.
    Contém informações sobre as dimensões do canal e observações adicionais.
    """
    __tablename__ = 'canal'
    id = Column(Integer, primary_key=True, autoincrement=True)
    valor = Column(String, nullable=False)
    largura = Column(Float)
    altura = Column(Float)
    comprimento_total = Column(Float)
    observacao = Column(String)

class Deducao(Base):
    """
    Representa a tabela de deduções no banco de dados.
    Relaciona canais, espessuras e materiais, armazenando o valor da dedução,
    observações e a força associada.
    """
    __tablename__ = 'deducao'
    id = Column(Integer, primary_key=True)
    canal_id = Column(Integer, ForeignKey('canal.id'), nullable=False)
    espessura_id = Column(Integer, ForeignKey('espessura.id'), nullable=False)
    material_id = Column(Integer, ForeignKey('material.id'), nullable=False)
    valor = Column(Float, nullable=False)
    observacao = Column(String)
    forca = Column(Float)

    canal = relationship("Canal")
    espessura = relationship("Espessura")
    material = relationship("Material")

    __table_args__ = (
        UniqueConstraint('canal_id',
                         'espessura_id',
                         'material_id',
                         name='_canal_espessura_material_uc'),
    )

class Log(Base):
    """
    Representa a tabela de logs no banco de dados.
    Armazena informações sobre ações realizadas no sistema, incluindo o nome do usuário,
    a ação executada, a tabela afetada, o ID do registro e detalhes adicionais.
    """
    __tablename__ = 'log'
    id = Column(Integer, primary_key=True)
    usuario_nome = Column(String, nullable=False)
    acao = Column(String, nullable=False)
    tabela = Column(String, nullable=False)
    registro_id = Column(Integer, nullable=False)
    detalhes = Column(String)
    data_hora = Column(DateTime, default=datetime.utcnow)

# Configuração do banco de dados
DATABASE_DIR = os.path.abspath("database")
makedirs(DATABASE_DIR, exist_ok=True)
engine = create_engine(
    f'sqlite:///{path.join(DATABASE_DIR, "tabela_de_dobra.db")}'
)
Base.metadata.create_all(engine)
