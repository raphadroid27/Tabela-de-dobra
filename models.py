from sqlalchemy import Column, Integer, String, Float, ForeignKey, create_engine
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class espessura(Base):
    __tablename__ = 'espessura'
    id = Column(Integer, primary_key=True)
    valor = Column(Float)

class material(Base):
    __tablename__ = 'material'
    id = Column(Integer, primary_key=True)
    nome = Column(String)
    densidade = Column(Float)

class canal(Base):
        __tablename__ = 'canal'
        id = Column(Integer, primary_key=True)
        valor = Column(Float)

class deducao(Base):
        __tablename__ = 'deducao'
        id = Column(Integer, primary_key=True)
        canal_id = Column(Integer, ForeignKey('canal.id'))
        espessura_id = Column(Integer, ForeignKey('espessura.id'))
        material_id = Column(Integer, ForeignKey('material.id'))
        valor = Column(Float)

        canal = relationship("canal")
        espessura = relationship("espessura")
        material = relationship("material")

engine = create_engine('sqlite:///tabela_de_dobra.db')
Base.metadata.create_all(engine)