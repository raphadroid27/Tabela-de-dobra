"""
Módulo de Operações de Dados

Este módulo contém a lógica pura para interagir com o banco de dados.
Todas as funções aqui são independentes da interface gráfica (UI) e são
responsáveis pelas operações CRUD (Criar, Ler, Atualizar, Excluir)
para os modelos da aplicação.

As funções retornam uma tupla padronizada:
(sucesso: bool, mensagem: str, objeto: object | None)
"""

import re
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.exc import SQLAlchemyError

from src.config import globals as g
from src.models.models import Canal, Deducao, Espessura, Material
from src.utils.banco_dados import registrar_log, tratativa_erro
from src.utils.banco_dados import session as db_session


def _converter_para_float(valor_str: Optional[str]) -> Optional[float]:
    """Converte uma string para float, tratando vírgulas e valores vazios."""
    if not valor_str or not valor_str.strip():
        return None
    try:
        return float(valor_str.replace(",", "."))
    except (ValueError, TypeError):
        return None


# --- Operações de Material ---


def criar_material(dados: Dict[str, Any]) -> Tuple[bool, str, Optional[Material]]:
    """
    Cria um novo material no banco de dados.

    Args:
        dados: Dicionário com os dados do material ('nome', 'densidade', etc.).

    Returns:
        Tupla (sucesso, mensagem, objeto_criado).
    """
    nome_material = dados.get("nome")
    if not nome_material:
        return False, "O nome do material é obrigatório.", None

    if db_session.query(Material).filter_by(nome=nome_material).first():
        return False, f"Material '{nome_material}' já existe.", None

    try:
        novo_material = Material(
            nome=nome_material,
            densidade=_converter_para_float(dados.get("densidade")),
            escoamento=_converter_para_float(dados.get("escoamento")),
            elasticidade=_converter_para_float(dados.get("elasticidade")),
        )
        db_session.add(novo_material)
        tratativa_erro()
        registrar_log(
            g.USUARIO_NOME,
            "adicionar",
            "material",
            novo_material.id,
            f"Material: {nome_material}",
        )
        return True, "Material adicionado com sucesso!", novo_material
    except SQLAlchemyError as e:
        db_session.rollback()
        return False, f"Erro de banco de dados ao criar material: {e}", None


# --- Operações de Espessura ---


def criar_espessura(valor: str) -> Tuple[bool, str, Optional[Espessura]]:
    """
    Cria uma nova espessura no banco de dados.

    Args:
        valor: O valor da espessura como string.

    Returns:
        Tupla (sucesso, mensagem, objeto_criado).
    """
    if not re.match(r"^\d+(\.\d+)?$", valor.replace(",", ".")):
        return False, "A espessura deve conter apenas números.", None

    espessura_float = _converter_para_float(valor)
    if espessura_float is None:
        return False, "Valor de espessura inválido.", None

    if db_session.query(Espessura).filter_by(valor=espessura_float).first():
        return False, "Espessura já existe no banco de dados.", None

    try:
        nova_espessura = Espessura(valor=espessura_float)
        db_session.add(nova_espessura)
        tratativa_erro()
        registrar_log(
            g.USUARIO_NOME,
            "adicionar",
            "espessura",
            nova_espessura.id,
            f"Valor: {espessura_float}",
        )
        return True, "Espessura adicionada com sucesso!", nova_espessura
    except SQLAlchemyError as e:
        db_session.rollback()
        return False, f"Erro de banco de dados ao criar espessura: {e}", None


# --- Operações de Canal ---


def criar_canal(dados: Dict[str, Any]) -> Tuple[bool, str, Optional[Canal]]:
    """
    Cria um novo canal no banco de dados.

    Args:
        dados: Dicionário com os dados do canal.

    Returns:
        Tupla (sucesso, mensagem, objeto_criado).
    """
    valor_canal = dados.get("valor")
    if not valor_canal:
        return False, "O campo Canal é obrigatório.", None

    if db_session.query(Canal).filter_by(valor=valor_canal).first():
        return False, "Canal já existe no banco de dados.", None

    try:
        novo_canal = Canal(
            valor=valor_canal,
            largura=_converter_para_float(dados.get("largura")),
            altura=_converter_para_float(dados.get("altura")),
            comprimento_total=_converter_para_float(dados.get("comprimento_total")),
            observacao=dados.get("observacao"),
        )
        db_session.add(novo_canal)
        tratativa_erro()
        registrar_log(
            g.USUARIO_NOME, "adicionar", "canal", novo_canal.id, f"Valor: {valor_canal}"
        )
        return True, "Canal adicionado com sucesso!", novo_canal
    except SQLAlchemyError as e:
        db_session.rollback()
        return False, f"Erro de banco de dados ao criar canal: {e}", None


# --- Operações de Dedução ---


def criar_deducao(dados: Dict[str, Any]) -> Tuple[bool, str, Optional[Deducao]]:
    """
    Cria uma nova dedução no banco de dados.

    Args:
        dados: Dicionário com os dados da dedução.

    Returns:
        Tupla (sucesso, mensagem, objeto_criado).
    """
    try:
        material_obj = (
            db_session.query(Material).filter_by(
                nome=dados.get("material_nome")).first()
        )
        espessura_obj = (
            db_session.query(Espessura)
            .filter_by(valor=_converter_para_float(dados.get("espessura_valor")))
            .first()
        )
        canal_obj = (
            db_session.query(Canal).filter_by(valor=dados.get("canal_valor")).first()
        )

        if not all([material_obj, espessura_obj, canal_obj]):
            return False, "Material, espessura ou canal não encontrado.", None

        deducao_existente = (
            db_session.query(Deducao)
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
        db_session.add(nova_deducao)
        tratativa_erro()
        detalhes = (
            f"Mat: {material_obj.nome}, Esp: {espessura_obj.valor}, "
            f"Canal: {canal_obj.valor}, Valor: {nova_deducao.valor}"
        )
        registrar_log(g.USUARIO_NOME, "adicionar", "dedução", nova_deducao.id, detalhes)
        return True, "Dedução adicionada com sucesso!", nova_deducao
    except (SQLAlchemyError, ValueError) as e:
        db_session.rollback()
        return False, f"Erro ao criar dedução: {e}", None


# --- Operações Genéricas de Exclusão ---


def excluir_objeto(obj: Any) -> Tuple[bool, str]:
    """
    Exclui um objeto do banco de dados e suas deduções relacionadas, se aplicável.

    Args:
        obj: O objeto SQLAlchemy a ser excluído.

    Returns:
        Tupla (sucesso, mensagem).
    """
    if obj is None:
        return False, "Objeto não encontrado para exclusão."

    obj_id = obj.id
    obj_type = type(obj).__name__.lower()
    obj_identifier = getattr(obj, "nome", None) or getattr(obj, "valor", "N/A")
    log_details = f"Excluído(a) {obj_type} {obj_identifier}"

    try:
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
            g.USUARIO_NOME, "excluir", obj_type, obj_id, log_details
        )

        mensagem = (
            "A dedução foi excluída com sucesso!"
            if obj_type == "deducao"
            else (
                f"{obj_type.capitalize()} e suas deduções relacionadas "
                f"foram excluídos(as) com sucesso!"
            )
        )
        return True, mensagem
    except SQLAlchemyError as e:
        db_session.rollback()
        return (False, f"Erro de banco de dados ao excluir {obj_type}: {e}")


# --- Operações de Edição ---
def editar_objeto(obj: Any, dados: Dict[str, Any]) -> Tuple[bool, str, list]:
    """
    Edita um objeto existente no banco de dados.

    Args:
        obj: O objeto SQLAlchemy a ser editado.
        dados: Dicionário com os novos dados.

    Returns:
        Tupla (sucesso, mensagem, lista_de_alteracoes).
    """
    if obj is None:
        return False, "Objeto não encontrado para edição.", []

    alteracoes = []

    try:
        db_session.add(obj)

        for campo, valor_novo_str in dados.items():
            valor_antigo = getattr(obj, campo)

            # CORREÇÃO: Define se um campo deve ser tratado como numérico
            # de forma mais inteligente, evitando a conversão incorreta para Canal.valor
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
            # O campo 'valor' só é numérico para Espessura e Deducao
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
                # Verifica se o campo é um identificador principal que não pode ser nulo
                if isinstance(obj, (Canal, Espessura, Deducao)) and campo == "valor":
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

        tratativa_erro()
        detalhes_log = "; ".join(alteracoes)
        registrar_log(
            g.USUARIO_NOME, "editar", type(obj).__name__.lower(), obj.id, detalhes_log
        )

        return (
            True,
            f"{type(obj).__name__.capitalize()} editado com sucesso!",
            alteracoes,
        )

    except (SQLAlchemyError, ValueError) as e:
        db_session.rollback()
        return False, f"Erro ao editar objeto: {e}", []
