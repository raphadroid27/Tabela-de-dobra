"""
Módulo de Operações de Dados (CRUD)
Versão corrigida para usar o context manager 'session_scope' e garantir
operações de banco de dados seguras em ambiente multi-thread.
"""

import re
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.exc import SQLAlchemyError

from src.config import globals as g
from src.models.models import Canal, Deducao, Espessura, Material

# REMOVIDO: session, tratativa_erro
# ADICIONADO: session_scope
from src.utils.banco_dados import registrar_log, session_scope


def _converter_para_float(valor_str: Optional[str]) -> Optional[float]:
    """Converte uma string para float, tratando vírgulas e valores vazios."""
    if not valor_str or not valor_str.strip():
        return None
    try:
        return float(valor_str.replace(",", "."))
    except (ValueError, TypeError):
        return None


def criar_material(dados: Dict[str, Any]) -> Tuple[bool, str, Optional[Material]]:
    """Cria um novo material no banco de dados."""
    nome_material = dados.get("nome")
    if not nome_material:
        return False, "O nome do material é obrigatório.", None

    try:
        with session_scope() as db_session:
            if db_session.query(Material).filter_by(nome=nome_material).first():
                return False, f"Material '{nome_material}' já existe.", None

            novo_material = Material(
                nome=nome_material,
                densidade=_converter_para_float(dados.get("densidade")),
                escoamento=_converter_para_float(dados.get("escoamento")),
                elasticidade=_converter_para_float(dados.get("elasticidade")),
            )
            db_session.add(novo_material)
            db_session.flush()  # Garante que o ID seja gerado para o log
            registrar_log(
                db_session,
                g.USUARIO_NOME,
                "adicionar",
                "material",
                novo_material.id,
                f"Material: {nome_material}",
            )
            return True, "Material adicionado com sucesso!", novo_material
    except SQLAlchemyError as e:
        return False, f"Erro de banco de dados ao criar material: {e}", None


def criar_espessura(valor: str) -> Tuple[bool, str, Optional[Espessura]]:
    """Cria uma nova espessura no banco de dados."""
    if not re.match(r"^\d+(\.\d+)?$", valor.replace(",", ".")):
        return False, "A espessura deve conter apenas números.", None

    espessura_float = _converter_para_float(valor)
    if espessura_float is None:
        return False, "Valor de espessura inválido.", None

    try:
        with session_scope() as db_session:
            if db_session.query(Espessura).filter_by(valor=espessura_float).first():
                return False, "Espessura já existe no banco de dados.", None

            nova_espessura = Espessura(valor=espessura_float)
            db_session.add(nova_espessura)
            db_session.flush()
            registrar_log(
                db_session,
                g.USUARIO_NOME,
                "adicionar",
                "espessura",
                nova_espessura.id,
                f"Valor: {espessura_float}",
            )
            return True, "Espessura adicionada com sucesso!", nova_espessura
    except SQLAlchemyError as e:
        return False, f"Erro de banco de dados ao criar espessura: {e}", None


def criar_canal(dados: Dict[str, Any]) -> Tuple[bool, str, Optional[Canal]]:
    """Cria um novo canal no banco de dados."""
    valor_canal = dados.get("valor")
    if not valor_canal:
        return False, "O campo Canal é obrigatório.", None

    try:
        with session_scope() as db_session:
            if db_session.query(Canal).filter_by(valor=valor_canal).first():
                return False, "Canal já existe no banco de dados.", None

            novo_canal = Canal(
                valor=valor_canal,
                largura=_converter_para_float(dados.get("largura")),
                altura=_converter_para_float(dados.get("altura")),
                comprimento_total=_converter_para_float(dados.get("comprimento_total")),
                observacao=dados.get("observacao"),
            )
            db_session.add(novo_canal)
            db_session.flush()
            registrar_log(
                db_session,
                g.USUARIO_NOME,
                "adicionar",
                "canal",
                novo_canal.id,
                f"Valor: {valor_canal}",
            )
            return True, "Canal adicionado com sucesso!", novo_canal
    except SQLAlchemyError as e:
        return False, f"Erro de banco de dados ao criar canal: {e}", None


def criar_deducao(dados: Dict[str, Any]) -> Tuple[bool, str, Optional[Deducao]]:
    """Cria uma nova dedução no banco de dados."""
    try:
        with session_scope() as db_session:
            material_obj = (
                db_session.query(Material)
                .filter_by(nome=dados.get("material_nome"))
                .first()
            )
            espessura_obj = (
                db_session.query(Espessura)
                .filter_by(valor=_converter_para_float(dados.get("espessura_valor")))
                .first()
            )
            canal_obj = (
                db_session.query(Canal)
                .filter_by(valor=dados.get("canal_valor"))
                .first()
            )

            if not all([material_obj, espessura_obj, canal_obj]):
                return False, "Material, espessura ou canal não encontrado.", None

            if (
                db_session.query(Deducao)
                .filter_by(
                    material_id=material_obj.id,
                    espessura_id=espessura_obj.id,
                    canal_id=canal_obj.id,
                )
                .first()
            ):
                return False, "Dedução já existe para esta combinação.", None

            nova_deducao = Deducao(
                material_id=material_obj.id,
                espessura_id=espessura_obj.id,
                canal_id=canal_obj.id,
                valor=_converter_para_float(dados.get("valor")),
                observacao=dados.get("observacao"),
                forca=_converter_para_float(dados.get("forca")),
            )
            db_session.add(nova_deducao)
            db_session.flush()
            detalhes = (
                f"Mat: {material_obj.nome}, Esp: {espessura_obj.valor}, "
                f"Canal: {canal_obj.valor}, Valor: {nova_deducao.valor}"
            )
            registrar_log(
                db_session,
                g.USUARIO_NOME,
                "adicionar",
                "dedução",
                nova_deducao.id,
                detalhes,
            )
            return True, "Dedução adicionada com sucesso!", nova_deducao
    except (SQLAlchemyError, ValueError) as e:
        return False, f"Erro ao criar dedução: {e}", None


def excluir_objeto(obj: Any) -> Tuple[bool, str]:
    """Exclui um objeto do banco de dados e suas deduções relacionadas."""
    if obj is None:
        return False, "Objeto não encontrado para exclusão."

    obj_id = obj.id
    obj_type = type(obj).__name__.lower()
    obj_identifier = getattr(obj, "nome", None) or getattr(obj, "valor", "N/A")
    log_details = f"Excluído(a) {obj_type} {obj_identifier}"

    try:
        with session_scope() as db_session:
            # Re-anexa o objeto à nova sessão para que o SQLAlchemy possa gerenciá-lo
            db_session.add(obj)

            if isinstance(obj, Material):
                db_session.query(Deducao).filter(Deducao.material_id == obj_id).delete(
                    synchronize_session=False
                )
            elif isinstance(obj, Espessura):
                db_session.query(Deducao).filter(Deducao.espessura_id == obj_id).delete(
                    synchronize_session=False
                )
            elif isinstance(obj, Canal):
                db_session.query(Deducao).filter(Deducao.canal_id == obj_id).delete(
                    synchronize_session=False
                )

            db_session.delete(obj)
            registrar_log(
                db_session, g.USUARIO_NOME, "excluir", obj_type, obj_id, log_details
            )
            return (
                True,
                (
                    (
                        "A dedução foi excluída com sucesso!"
                        if obj_type == "deducao"
                        else f"{obj_type.capitalize()} e suas deduções "
                        f"relacionadas foram excluídos(as) com sucesso!"
                    ),
                ),
            )
    except SQLAlchemyError as e:
        return False, f"Erro de banco de dados ao excluir {obj_type}: {e}"


def editar_objeto(obj: Any, dados: Dict[str, Any]) -> Tuple[bool, str, list]:
    """Edita um objeto existente no banco de dados."""
    if obj is None:
        return False, "Objeto não encontrado para edição.", []

    alteracoes = []
    campos_numericos = [
        "largura",
        "altura",
        "comprimento_total",
        "valor",
        "densidade",
        "escoamento",
        "elasticidade",
        "forca",
    ]

    try:
        with session_scope() as db_session:
            # Re-anexa o objeto à nova sessão
            db_session.add(obj)

            for campo, valor_novo_str in dados.items():
                valor_antigo = getattr(obj, campo)
                valor_novo = (
                    _converter_para_float(valor_novo_str)
                    if campo in campos_numericos
                    else (
                        valor_novo_str
                        if valor_novo_str and valor_novo_str.strip()
                        else None
                    )
                )

                if str(valor_antigo) != str(valor_novo):
                    setattr(obj, campo, valor_novo)
                    alteracoes.append(f"{campo}: '{valor_antigo}' -> '{valor_novo}'")

            if not alteracoes:
                return True, "Nenhuma alteração detectada.", []

            detalhes_log = "; ".join(alteracoes)
            registrar_log(
                db_session,
                g.USUARIO_NOME,
                "editar",
                type(obj).__name__.lower(),
                obj.id,
                detalhes_log,
            )
            return (
                True,
                f"{type(obj).__name__.capitalize()} editado com sucesso!",
                alteracoes,
            )
    except (SQLAlchemyError, ValueError) as e:
        return False, f"Erro ao editar objeto: {e}", []
