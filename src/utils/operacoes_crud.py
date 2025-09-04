"""
Módulo de Operações de Dados (Refatorado)

Este módulo foi atualizado para usar o padrão de "sessão por operação"
e integração com cache para melhor performance e resiliência.
Cada função agora gerencia seu próprio ciclo de vida da sessão,
garantindo que as transações sejam curtas e o banco de dados
seja liberado rapidamente.
"""

import logging
import re
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.exc import SQLAlchemyError

from src.config import globals as g
from src.models.models import Canal, Deducao, Espessura, Material
from src.utils.banco_dados import get_session, registrar_log


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
        with get_session() as session:
            if session.query(Material).filter_by(nome=nome_material).first():
                return False, f"Material '{nome_material}' já existe.", None

            novo_material = Material(
                nome=nome_material,
                densidade=_converter_para_float(dados.get("densidade")),
                escoamento=_converter_para_float(dados.get("escoamento")),
                elasticidade=_converter_para_float(dados.get("elasticidade")),
            )
            session.add(novo_material)
            session.flush()  # Garante que novo_material.id esteja disponível
            registrar_log(
                session,
                g.USUARIO_NOME,
                "adicionar",
                "material",
                novo_material.id,
                f"Material: {nome_material}",
            )

        # Invalida cache após adicionar material
        try:
            # Import local para evitar dependência circular
            from src.utils.cache_manager import (  # pylint: disable=import-outside-toplevel
                cache_manager,
            )

            cache_manager.invalidate_cache(["materiais"])
            logging.info("Cache de materiais invalidado após adição")
        except (ImportError, AttributeError, RuntimeError) as e:
            logging.warning("Erro ao invalidar cache de materiais: %s", e)

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
        with get_session() as session:
            if session.query(Espessura).filter_by(valor=espessura_float).first():
                return False, "Espessura já existe no banco de dados.", None

            nova_espessura = Espessura(valor=espessura_float)
            session.add(nova_espessura)
            session.flush()
            registrar_log(
                session,
                g.USUARIO_NOME,
                "adicionar",
                "espessura",
                nova_espessura.id,
                f"Valor: {espessura_float}",
            )

        # Invalida cache após adicionar espessura
        try:
            # Import local para evitar dependência circular
            from src.utils.cache_manager import (  # pylint: disable=import-outside-toplevel
                cache_manager,
            )

            cache_manager.invalidate_cache(["espessuras"])
            logging.info("Cache de espessuras invalidado após adição")
        except (ImportError, AttributeError, RuntimeError) as e:
            logging.warning("Erro ao invalidar cache de espessuras: %s", e)

        return True, "Espessura adicionada com sucesso!", nova_espessura
    except SQLAlchemyError as e:
        return False, f"Erro de banco de dados ao criar espessura: {e}", None


def criar_canal(dados: Dict[str, Any]) -> Tuple[bool, str, Optional[Canal]]:
    """Cria um novo canal no banco de dados."""
    valor_canal = dados.get("valor")
    if not valor_canal:
        return False, "O campo Canal é obrigatório.", None

    try:
        with get_session() as session:
            if session.query(Canal).filter_by(valor=valor_canal).first():
                return False, "Canal já existe no banco de dados.", None

            novo_canal = Canal(
                valor=valor_canal,
                largura=_converter_para_float(dados.get("largura")),
                altura=_converter_para_float(dados.get("altura")),
                comprimento_total=_converter_para_float(dados.get("comprimento_total")),
                observacao=dados.get("observacao"),
            )
            session.add(novo_canal)
            session.flush()
            registrar_log(
                session,
                g.USUARIO_NOME,
                "adicionar",
                "canal",
                novo_canal.id,
                f"Valor: {valor_canal}",
            )

        # Invalida cache após adicionar canal
        try:
            # Import local para evitar dependência circular
            from src.utils.cache_manager import (  # pylint: disable=import-outside-toplevel
                cache_manager,
            )

            cache_manager.invalidate_cache(["canais"])
            logging.info("Cache de canais invalidado após adição")
        except (ImportError, AttributeError, RuntimeError) as e:
            logging.warning("Erro ao invalidar cache de canais: %s", e)

        return True, "Canal adicionado com sucesso!", novo_canal
    except SQLAlchemyError as e:
        return False, f"Erro de banco de dados ao criar canal: {e}", None


def criar_deducao(dados: Dict[str, Any]) -> Tuple[bool, str, Optional[Deducao]]:
    """Cria uma nova dedução no banco de dados."""
    try:
        with get_session() as session:
            material_obj = (
                session.query(Material)
                .filter_by(nome=dados.get("material_nome"))
                .first()
            )
            espessura_obj = (
                session.query(Espessura)
                .filter_by(valor=_converter_para_float(dados.get("espessura_valor")))
                .first()
            )
            canal_obj = (
                session.query(Canal).filter_by(valor=dados.get("canal_valor")).first()
            )

            if not all([material_obj, espessura_obj, canal_obj]):
                return False, "Material, espessura ou canal não encontrado.", None

            deducao_existente = (
                session.query(Deducao)
                .filter_by(
                    material_id=material_obj.id,
                    espessura_id=espessura_obj.id,
                    canal_id=canal_obj.id,
                )
                .first()
            )

            if deducao_existente:
                return False, "Dedução já existe para esta combinação.", None

            nova_deducao = Deducao(
                material_id=material_obj.id,
                espessura_id=espessura_obj.id,
                canal_id=canal_obj.id,
                valor=_converter_para_float(dados.get("valor")),
                observacao=dados.get("observacao"),
                forca=_converter_para_float(dados.get("forca")),
            )
            session.add(nova_deducao)
            session.flush()
            detalhes = (
                f"Mat: {material_obj.nome}, Esp: {espessura_obj.valor}, "
                f"Canal: {canal_obj.valor}, Valor: {nova_deducao.valor}"
            )
            registrar_log(
                session,
                g.USUARIO_NOME,
                "adicionar",
                "dedução",
                nova_deducao.id,
                detalhes,
            )

        # Invalida cache após adicionar dedução
        try:
            # Import local para evitar dependência circular
            from src.utils.cache_manager import (  # pylint: disable=import-outside-toplevel
                cache_manager,
            )

            cache_manager.invalidate_cache(["deducoes"])
            logging.info("Cache de deduções invalidado após adição")
        except (ImportError, AttributeError, RuntimeError) as e:
            logging.warning("Erro ao invalidar cache de deduções: %s", e)

        return True, "Dedução adicionada com sucesso!", nova_deducao
    except (SQLAlchemyError, ValueError) as e:
        return False, f"Erro ao criar dedução: {e}", None


def excluir_objeto(obj_id: int, obj_type: type) -> Tuple[bool, str]:
    """Exclui um objeto do banco de dados pelo seu ID e tipo."""
    try:
        with get_session() as session:
            obj = session.get(obj_type, obj_id)
            if obj is None:
                return False, "Objeto não encontrado para exclusão."

            obj_identifier = getattr(obj, "nome", None) or getattr(obj, "valor", "N/A")
            log_details = f"Excluído(a) {obj_type.__name__.lower()} {obj_identifier}"

            if isinstance(obj, Material):
                session.query(Deducao).filter(Deducao.material_id == obj.id).delete()
            elif isinstance(obj, Espessura):
                session.query(Deducao).filter(Deducao.espessura_id == obj.id).delete()
            elif isinstance(obj, Canal):
                session.query(Deducao).filter(Deducao.canal_id == obj.id).delete()

            session.delete(obj)
            registrar_log(
                session,
                g.USUARIO_NOME,
                "excluir",
                obj_type.__name__.lower(),
                obj_id,
                log_details,
            )

            mensagem = (
                "A dedução foi excluída com sucesso!"
                if obj_type is Deducao
                else f"{obj_type.__name__.capitalize()} e suas deduções relacionadas foram excluídos(as)!"  # pylint: disable=C0301
            )

        # Invalida cache após exclusão
        try:
            # Import local para evitar dependência circular
            from src.utils.cache_manager import (  # pylint: disable=import-outside-toplevel
                cache_manager,
            )

            # Mapeia tipos para cache
            cache_keys = {
                Material: ["materiais", "deducoes"],
                Espessura: ["espessuras", "deducoes"],
                Canal: ["canais", "deducoes"],
                Deducao: ["deducoes"],
            }

            keys_to_invalidate = cache_keys.get(obj_type, [])
            if keys_to_invalidate:
                cache_manager.invalidate_cache(keys_to_invalidate)
                logging.info("Cache invalidado após exclusão: %s", keys_to_invalidate)

        except (ImportError, AttributeError, RuntimeError) as e:
            logging.warning("Erro ao invalidar cache após exclusão: %s", e)

        return True, mensagem
    except SQLAlchemyError as e:
        return False, f"Erro de banco de dados ao excluir: {e}"


def editar_objeto(  # pylint: disable=too-many-locals,too-many-branches
    obj_id: int, obj_type: type, dados: Dict[str, Any]
) -> Tuple[bool, str, list]:
    """Edita um objeto existente no banco de dados."""
    alteracoes = []
    try:
        with get_session() as session:
            obj = session.get(obj_type, obj_id)
            if obj is None:
                return False, "Objeto não encontrado para edição.", []

            for campo, valor_novo_str in dados.items():
                valor_antigo = getattr(obj, campo)

                is_numeric = False
                campos_numericos_gerais = [
                    "largura",
                    "altura",
                    "comprimento_total",
                    "densidade",
                    "escoamento",
                    "elasticidade",
                    "forca",
                ]
                if campo in campos_numericos_gerais:
                    is_numeric = True
                if campo == "valor" and not isinstance(obj, Canal):
                    is_numeric = True

                valor_novo = (
                    _converter_para_float(valor_novo_str)
                    if is_numeric
                    else (
                        valor_novo_str
                        if valor_novo_str and valor_novo_str.strip()
                        else None
                    )
                )

                if valor_novo is None:
                    is_required = False
                    if (
                        isinstance(obj, (Canal, Espessura, Deducao))
                        and campo == "valor"
                    ):
                        is_required = True
                    if isinstance(obj, Material) and campo == "nome":
                        is_required = True
                    if is_required:
                        return (
                            False,
                            f"O campo '{campo.capitalize()}' não pode ser vazio.",
                            [],
                        )

                if str(valor_antigo) != str(valor_novo):
                    setattr(obj, campo, valor_novo)
                    alteracoes.append(f"{campo}: '{valor_antigo}' -> '{valor_novo}'")

            if not alteracoes:
                return True, "Nenhuma alteração detectada.", []

            detalhes_log = "; ".join(alteracoes)
            registrar_log(
                session,
                g.USUARIO_NOME,
                "editar",
                type(obj).__name__.lower(),
                obj.id,
                detalhes_log,
            )

        # Invalida cache após edição
        try:
            # Import local para evitar dependência circular
            from src.utils.cache_manager import (  # pylint: disable=import-outside-toplevel
                cache_manager,
            )

            # Mapeia tipos para cache
            cache_keys = {
                Material: ["materiais", "deducoes"],
                Espessura: ["espessuras", "deducoes"],
                Canal: ["canais", "deducoes"],
                Deducao: ["deducoes"],
            }

            keys_to_invalidate = cache_keys.get(type(obj), [])
            if keys_to_invalidate:
                cache_manager.invalidate_cache(keys_to_invalidate)
                logging.info("Cache invalidado após edição: %s", keys_to_invalidate)

        except (ImportError, AttributeError, RuntimeError) as e:
            logging.warning("Erro ao invalidar cache após edição: %s", e)

        return (
            True,
            f"{type(obj).__name__.capitalize()} editado com sucesso!",
            alteracoes,
        )
    except (SQLAlchemyError, ValueError) as e:
        return False, f"Erro ao editar objeto: {e}", []
