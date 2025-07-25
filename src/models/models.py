"""
Modelo de dados para o sistema de cálculo de dobra de chapas.

Este módulo define as classes que representam as tabelas do banco de dados,
utilizando SQLAlchemy para ORM.
"""

import os
import sys
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey, DateTime, create_engine,
    UniqueConstraint
)
from sqlalchemy.orm import relationship, sessionmaker, declarative_base

# --- Configuração de Caminhos de Forma Robusta ---


def get_base_dir() -> str:
    """Retorna o diretório base da aplicação, seja em modo script ou executável."""
    if getattr(sys, 'frozen', False):
        # Se o aplicativo for um executável (gerado por PyInstaller, por exemplo),
        # o diretório base é onde o executável está localizado.
        return os.path.dirname(sys.executable)
    # Em modo de script, assume que este arquivo está em 'src/models',
    # então o diretório base está dois níveis acima.
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


BASE_DIR = get_base_dir()
DATABASE_DIR = os.path.join(BASE_DIR, "database")

# Garante que o diretório do banco de dados exista.
os.makedirs(DATABASE_DIR, exist_ok=True)
DB_PATH = os.path.join(DATABASE_DIR, "tabela_de_dobra.db")

# --- Modelos ORM ---

Base = declarative_base()


class Usuario(Base):
    """Modelo da tabela de usuários."""
    __tablename__ = 'usuario'
    id = Column(Integer, primary_key=True)
    nome = Column(String, unique=True, nullable=False)
    senha = Column(String, nullable=False)
    role = Column(String, default="viewer")


class Espessura(Base):
    """Modelo da tabela de espessuras."""
    __tablename__ = 'espessura'
    id = Column(Integer, primary_key=True, autoincrement=True)
    valor = Column(Float, nullable=False)


class Material(Base):
    """Modelo da tabela de materiais."""
    __tablename__ = 'material'
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    densidade = Column(Float)
    escoamento = Column(Float)
    elasticidade = Column(Float)


class Canal(Base):
    """Modelo da tabela de canais (ferramentas)."""
    __tablename__ = 'canal'
    id = Column(Integer, primary_key=True, autoincrement=True)
    valor = Column(String, nullable=False)
    largura = Column(Float)
    altura = Column(Float)
    comprimento_total = Column(Float)
    observacao = Column(String)


class Deducao(Base):
    """Modelo da tabela de deduções, relacionando os outros elementos."""
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
        UniqueConstraint('canal_id', 'espessura_id', 'material_id',
                         name='_canal_espessura_material_uc'),
    )


class Log(Base):
    """Modelo da tabela de logs de ações do sistema."""
    __tablename__ = 'log'
    id = Column(Integer, primary_key=True)
    usuario_nome = Column(String, nullable=False)
    acao = Column(String, nullable=False)
    tabela = Column(String, nullable=False)
    registro_id = Column(Integer, nullable=False)
    detalhes = Column(String)
    data_hora = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SystemControl(Base):
    """
    Tabela de controle do sistema para atualizações e sessões ativas.
    """
    __tablename__ = 'system_control'
    id = Column(Integer, primary_key=True)
    type = Column(String, nullable=False)
    key = Column(String, unique=True, nullable=False)
    value = Column(String)
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                          onupdate=lambda: datetime.now(timezone.utc))


# --- Configuração do Banco de Dados e Sessão ---
engine = create_engine(f'sqlite:///{DB_PATH}')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
