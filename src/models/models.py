# -*- coding: utf-8 -*-
"""
Modelo de dados para o sistema de cálculo de dobra de chapas.

Este módulo define as classes que representam as tabelas do banco de dados,
utilizando SQLAlchemy para ORM.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship

from src.utils.utilitarios import DB_PATH

# --- Modelos ORM ---

Base = declarative_base()


class Usuario(Base):
    """Modelo da tabela de usuários."""

    __tablename__ = "usuario"
    id = Column(Integer, primary_key=True)
    nome = Column(String, unique=True, nullable=False)
    senha = Column(String, nullable=False)
    role = Column(String, default="viewer")


class Espessura(Base):
    """Modelo da tabela de espessuras."""

    __tablename__ = "espessura"
    id = Column(Integer, primary_key=True, autoincrement=True)
    valor = Column(Float, nullable=False)


class Material(Base):
    """Modelo da tabela de materiais."""

    __tablename__ = "material"
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    densidade = Column(Float)
    escoamento = Column(Float)
    elasticidade = Column(Float)


class Canal(Base):
    """Modelo da tabela de canais (ferramentas)."""

    __tablename__ = "canal"
    id = Column(Integer, primary_key=True, autoincrement=True)
    valor = Column(String, nullable=False)
    largura = Column(Float)
    altura = Column(Float)
    comprimento_total = Column(Float)
    observacao = Column(String)


class Deducao(Base):
    """Modelo da tabela de deduções, relacionando os outros elementos."""

    __tablename__ = "deducao"
    id = Column(Integer, primary_key=True)
    canal_id = Column(Integer, ForeignKey("canal.id"), nullable=False)
    espessura_id = Column(Integer, ForeignKey("espessura.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("material.id"), nullable=False)
    valor = Column(Float, nullable=False)
    observacao = Column(String)
    forca = Column(Float)

    canal = relationship("Canal")
    espessura = relationship("Espessura")
    material = relationship("Material")

    __table_args__ = (
        UniqueConstraint(
            "canal_id",
            "espessura_id",
            "material_id",
            name="_canal_espessura_material_uc",
        ),
    )


class Log(Base):
    """Modelo da tabela de logs de ações do sistema."""

    __tablename__ = "log"
    id = Column(Integer, primary_key=True)
    usuario_nome = Column(String, nullable=False)
    acao = Column(String, nullable=False)
    tabela = Column(String, nullable=False)
    registro_id = Column(Integer, nullable=False)
    detalhes = Column(String)
    data_hora = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SystemControl(Base):
    """Tabela de controle do sistema para atualizações e sessões ativas."""

    __tablename__ = "system_control"
    id = Column(Integer, primary_key=True)
    type = Column(String, nullable=False)  # pylint: disable=redefined-builtin
    key = Column(String, unique=True, nullable=False)
    value = Column(String)
    last_updated = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


engine = create_engine(f"sqlite:///{DB_PATH}")
