"""
Módulo de Cálculos para o Aplicativo de Dobras.

Este módulo contém todas as funções e classes responsáveis por realizar
os cálculos matemáticos e lógicos do sistema. As funções aqui presentes
recebem dados brutos como argumentos, processam-nos e retornam os resultados,
sem modificar ou sequer conhecer a interface gráfica.
"""

import re
from math import pi
from typing import List

from sqlalchemy.exc import SQLAlchemyError

from src.config import globals as g
from src.models.models import Canal, Deducao, Espessura, Material
from src.utils.banco_dados import get_session


def buscar_deducao_por_parametros(
    session, material_nome: str, espessura_valor: float, canal_valor: str
):
    """
    Busca uma dedução no banco de dados usando os parâmetros fornecidos.

    Args:
        session: Sessão do SQLAlchemy
        material_nome: Nome do material
        espessura_valor: Valor da espessura (float)
        canal_valor: Valor do canal

    Returns:
        Objeto Deducao ou None se não encontrado
    """
    return (
        session.query(Deducao)
        .join(Material)
        .join(Espessura)
        .join(Canal)
        .filter(
            Material.nome == material_nome,
            Espessura.valor == espessura_valor,
            Canal.valor == canal_valor,
        )
        .first()
    )


def converter_para_float(valor_str: str, default_value: float = 0.0) -> float:
    """Converte uma string para float, tratando vírgulas e valores vazios."""
    if not isinstance(valor_str, str) or not valor_str.strip():
        return default_value
    try:
        return float(valor_str.replace(" Copiado!", "").replace(",", "."))
    except (ValueError, TypeError):
        return default_value


def _extrair_valor_canal(canal_str):
    """Extrai o valor numérico de uma string de canal."""
    if not canal_str:
        return None
    numeros = re.findall(r"\d+\.?\d*", canal_str)
    return float(numeros[0]) if numeros else None


class CalculoDeducaoDB:
    """Busca a dedução e observação do banco de dados."""

    def buscar(self, material_nome: str, espessura_str: str, canal_valor: str):
        """Busca a dedução no banco de dados."""
        if not all([material_nome, espessura_str, canal_valor]):
            return None

        try:
            with get_session() as session:
                espessura_valor_float = float(espessura_str)
                resultado = buscar_deducao_por_parametros(
                    session, material_nome, espessura_valor_float, canal_valor
                )

                if resultado:
                    return {"valor": resultado.valor, "obs": resultado.observacao or ""}
                return {"valor": "N/A", "obs": "Dedução não encontrada."}

        except (SQLAlchemyError, ValueError, TypeError):
            return None


class CalculoFatorK:
    """Calcula o Fator K e o Offset."""

    @staticmethod
    def _formula_fator_k(espessura, deducao, raio_interno):
        """Fórmula para calcular o Fator K."""
        if espessura == 0:
            return 0.0
        numerador = 4 * (espessura - (deducao / 2) + raio_interno) - (pi * raio_interno)
        denominador = pi * espessura
        fator_k = numerador / denominador if denominador != 0 else 0
        return max(0.0, min(fator_k, 0.5))

    @staticmethod
    def _obter_fator_k_tabela(razao_re):
        """Obtém o fator K da tabela de referência por interpolação."""
        razao_re = max(0.1, min(razao_re, 10.0))
        if razao_re in g.RAIO_K:
            return g.RAIO_K[razao_re]

        razoes = sorted(g.RAIO_K.keys())
        for i in range(len(razoes) - 1):
            r1, r2 = razoes[i], razoes[i + 1]
            if r1 <= razao_re <= r2:
                k1, k2 = g.RAIO_K[r1], g.RAIO_K[r2]
                return k1 + (k2 - k1) * (razao_re - r1) / (r2 - r1)
        return g.RAIO_K[razoes[-1]]

    def calcular(self, espessura: float, raio_interno: float, deducao_usada: float):
        """Executa o cálculo do Fator K e Offset."""
        if raio_interno <= 0 or espessura <= 0:
            return None

        if deducao_usada > 0:
            fator_k = self._formula_fator_k(espessura, deducao_usada, raio_interno)
        else:
            razao_re = raio_interno / espessura if espessura > 0 else 0
            fator_k = self._obter_fator_k_tabela(razao_re)

        offset = fator_k * espessura
        return {"fator_k": fator_k, "offset": offset}


class CalculoAbaMinima:
    """Calcula a aba mínima externa."""

    def calcular(self, canal_str: str, espessura: float):
        """Executa o cálculo da aba mínima externa."""
        if not canal_str or espessura <= 0:
            return None
        valor_canal = _extrair_valor_canal(canal_str)
        if valor_canal is None:
            return None
        return (valor_canal / 2) + espessura + 2


class CalculoZMinimo:
    """Calcula o Z mínimo externo."""

    def calcular(self, espessura: float, deducao: float, canal_str: str):
        """Executa o cálculo do Z mínimo externo."""
        if espessura <= 0 or deducao <= 0 or not canal_str:
            return None
        try:
            with get_session() as session:
                canal_obj = session.query(Canal).filter_by(valor=canal_str).first()
                if not canal_obj or canal_obj.largura is None:
                    return None
                return espessura + (deducao / 2) + (canal_obj.largura / 2) + 2
        except SQLAlchemyError:
            return None


class CalculoRazaoRIE:
    """Calcula a razão entre Raio Interno e Espessura."""

    def calcular(self, espessura: float, raio_interno: float):
        """Executa o cálculo da razão RI/E."""
        if espessura <= 0 or raio_interno <= 0:
            return None
        razao = raio_interno / espessura
        return min(razao, 10.0)


class CalculoForca:
    """Calcula a força de dobra necessária."""

    @staticmethod
    def _obter_forca_db(session, espessura_valor, material_nome, canal_valor):
        """Busca o valor da força no banco de dados."""

        deducao_obj = (
            # pylint: disable=R0801
            session.query(Deducao)
            .join(Material)
            .join(Espessura)
            .join(Canal)
            .filter(
                Material.nome == material_nome,
                Espessura.valor == espessura_valor,
                Canal.valor == canal_valor,
            )
            .first()
        )
        canal_obj = session.query(Canal).filter_by(valor=canal_valor).first()
        return (deducao_obj.forca if deducao_obj else None), canal_obj

    def calcular(self, comprimento: float, espessura: float, material: str, canal: str):
        """Executa o cálculo da força em toneladas/m."""
        if not all([espessura, material, canal]):
            return None
        try:
            with get_session() as session:
                forca_base, canal_obj = self._obter_forca_db(
                    session, espessura, material, canal
                )
                if forca_base is None:
                    return {"forca": None, "canal_obj": None, "comprimento_total": None}
                toneladas_m = (
                    (forca_base * comprimento) / 1000 if comprimento > 0 else forca_base
                )
                # Extrair o valor do comprimento_total antes de fechar a sessão
                comprimento_total = canal_obj.comprimento_total if canal_obj else None
                return {
                    "forca": toneladas_m,
                    "canal_obj": canal_obj,
                    "comprimento_total": comprimento_total,
                }
        except SQLAlchemyError:
            return {"forca": None, "canal_obj": None, "comprimento_total": None}


class CalculoDobra:
    """Calcula as medidas de dobra, metade e blank."""

    @staticmethod
    def _calcular_medida_individual(
        valor_dobra, deducao, pos_atual, blocos_preenchidos
    ):
        """Calcula a medida de uma única dobra."""
        for bloco in blocos_preenchidos:
            if pos_atual in bloco:
                pos_no_bloco = bloco.index(pos_atual)
                if len(bloco) == 1 or pos_no_bloco in (0, len(bloco) - 1):
                    return valor_dobra - deducao / 2
                return valor_dobra - deducao
        return 0.0

    def calcular_coluna(self, valores_dobras: List[float], deducao: float):
        """Calcula todas as dobras e o blank para uma coluna."""
        if deducao <= 0:
            return None

        preenchidos = [v > 0 for v in valores_dobras]
        blocos, bloco_atual = [], []
        for i, preenchido in enumerate(preenchidos):
            if preenchido:
                bloco_atual.append(i)
            elif bloco_atual:
                blocos.append(bloco_atual)
                bloco_atual = []
        if bloco_atual:
            blocos.append(bloco_atual)

        resultados, blank_total = [], 0
        for i, dobra_valor in enumerate(valores_dobras):
            if dobra_valor <= 0:
                resultados.append({"medida": None, "metade": None})
                continue
            medida = self._calcular_medida_individual(dobra_valor, deducao, i, blocos)
            metade = medida / 2
            blank_total += medida
            resultados.append({"medida": medida, "metade": metade})
        return {"resultados": resultados, "blank_total": blank_total}
