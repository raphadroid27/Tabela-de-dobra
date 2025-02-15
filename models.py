from sqlalchemy import Column, Integer, String, Float, ForeignKey, create_engine, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class usuario(Base):
    __tablename__ = 'usuario'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String)
    senha = Column(String)
    admin = Column(Integer)

class espessura(Base):
    __tablename__ = 'espessura'
    id = Column(Integer, primary_key=True, autoincrement=True)
    valor = Column(Float)

class material(Base):
    __tablename__ = 'material'
    id = Column(Integer, primary_key=True)
    nome = Column(String)
    densidade = Column(Float)
    escoamento = Column(Float)
    elasticidade = Column(Float)

class canal(Base):
    __tablename__ = 'canal'
    id = Column(Integer, primary_key=True, autoincrement=True)
    valor = Column(String)
    largura = Column(Float)
    altura = Column(Float)
    comprimento_total = Column(Float)
    observacao = Column(String)

class deducao(Base):
    __tablename__ = 'deducao'
    id = Column(Integer, primary_key=True)
    canal_id = Column(Integer, ForeignKey('canal.id'))
    espessura_id = Column(Integer, ForeignKey('espessura.id'))
    material_id = Column(Integer, ForeignKey('material.id'))
    valor = Column(Float)
    observacao = Column(String)
    forca = Column(Float)

    canal = relationship("canal")
    espessura = relationship("espessura")
    material = relationship("material")

    __table_args__ = (UniqueConstraint('canal_id', 'espessura_id', 'material_id', name='_canal_espessura_material_uc'),)

engine = create_engine('sqlite:///tabela_de_dobra.db')
Base.metadata.create_all(engine)