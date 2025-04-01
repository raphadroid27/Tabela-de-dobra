from sqlalchemy import Column, Integer, String, Float, ForeignKey,DateTime, create_engine, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Usuario(Base):  # Ajustado para PascalCase
    __tablename__ = 'usuario'
    id = Column(Integer, primary_key=True)
    nome = Column(String, unique=True, nullable=False)
    senha = Column(String, nullable=False)
    admin = Column(Boolean, default=False, nullable=False)  # Adicionado nullable=False

class Espessura(Base):  # Ajustado para PascalCase
    __tablename__ = 'espessura'
    id = Column(Integer, primary_key=True, autoincrement=True)
    valor = Column(Float, nullable=False)  # Adicionado nullable=False

class Material(Base):  # Ajustado para PascalCase
    __tablename__ = 'material'
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)  # Adicionado nullable=False
    densidade = Column(Float)
    escoamento = Column(Float)
    elasticidade = Column(Float)

class Canal(Base):  # Ajustado para PascalCase
    __tablename__ = 'canal'
    id = Column(Integer, primary_key=True, autoincrement=True)
    valor = Column(String, nullable=False)  # Adicionado nullable=False
    largura = Column(Float)
    altura = Column(Float)
    comprimento_total = Column(Float)
    observacao = Column(String)

class Deducao(Base):  # Ajustado para PascalCase
    __tablename__ = 'deducao'
    id = Column(Integer, primary_key=True)
    canal_id = Column(Integer, ForeignKey('canal.id'), nullable=False)  # Adicionado nullable=False
    espessura_id = Column(Integer, ForeignKey('espessura.id'), nullable=False)  # Adicionado nullable=False
    material_id = Column(Integer, ForeignKey('material.id'), nullable=False)  # Adicionado nullable=False
    valor = Column(Float, nullable=False)  # Adicionado nullable=False
    observacao = Column(String)
    forca = Column(Float)

    canal = relationship("Canal")
    espessura = relationship("Espessura")
    material = relationship("Material")

    __table_args__ = (UniqueConstraint('canal_id', 'espessura_id', 'material_id', name='_canal_espessura_material_uc'),)

class Log(Base):
    __tablename__ = 'log'
    id = Column(Integer, primary_key=True)
    usuario_nome = Column(String, nullable=False)
    acao = Column(String, nullable=False)
    tabela = Column(String, nullable=False)
    registro_id = Column(Integer, nullable=False)
    detalhes = Column(String)  # Adicionado para armazenar os detalhes das alterações
    data_hora = Column(DateTime, default=datetime.utcnow)

engine = create_engine('sqlite:///tabela_de_dobra.db')
Base.metadata.create_all(engine)