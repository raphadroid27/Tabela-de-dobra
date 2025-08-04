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

from src.config import globals as g
from src.models.models import Canal, Deducao, Espessura, Material
from src.utils.banco_dados import session

# --- FUNÇÕES DE CONVERSÃO DE DADOS ---


def converter_para_float(valor_str: str, default_value: float = 0.0) -> float:
    """
    Converte uma string para float, tratando vírgulas e valores vazios.

    Args:
        valor_str (str): A string a ser convertida.
        default_value (float): Valor padrão em caso de falha na conversão.

    Returns:
        float: O valor convertido.
    """
    if not isinstance(valor_str, str) or not valor_str.strip():
        return default_value
    try:
        # Remove " Copiado!" e substitui vírgula por ponto
        return float(valor_str.replace(" Copiado!", "").replace(",", "."))
    except (ValueError, TypeError):
        return default_value


# --- CLASSES DE CÁLCULO (INDEPENDENTES DA UI) ---


class CalculoDeducaoDB:
    """Busca a dedução e observação do banco de dados."""

    def buscar(self, material_nome: str, espessura_str: str, canal_valor: str):
        """
        Busca a dedução no banco de dados com base nos valores fornecidos.

        Returns:
            dict: {'valor': float/str, 'obs': str} ou None
        """
        if not all([material_nome, espessura_str, canal_valor]):
            return None

        try:
            espessura_valor = float(espessura_str)
            espessura_obj = (
                session.query(Espessura).filter_by(valor=espessura_valor).first()
            )
            material_obj = session.query(Material).filter_by(nome=material_nome).first()
            canal_obj = session.query(Canal).filter_by(valor=canal_valor).first()

            if not all([espessura_obj, material_obj, canal_obj]):
                return {"valor": "N/A", "obs": "Combinação não encontrada."}

            deducao_obj = (
                session.query(Deducao)
                .filter(
                    Deducao.espessura_id == espessura_obj.id,
                    Deducao.material_id == material_obj.id,
                    Deducao.canal_id == canal_obj.id,
                )
                .first()
            )

            if deducao_obj:
                return {"valor": deducao_obj.valor, "obs": deducao_obj.observacao or ""}

            return {"valor": "N/A", "obs": "Dedução não encontrada."}

        except (ValueError, TypeError):
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
        """
        Executa o cálculo do Fator K e Offset.
        """
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

    @staticmethod
    def _extrair_valor_canal(canal_str):
        """Extrai o valor numérico de uma string de canal."""
        if not canal_str:
            return None
        numeros = re.findall(r"\d+\.?\d*", canal_str)
        return float(numeros[0]) if numeros else None

    def calcular(self, canal_str: str, espessura: float):
        """
        Executa o cálculo da aba mínima externa.
        """
        if not canal_str or espessura <= 0:
            return None

        valor_canal = self._extrair_valor_canal(canal_str)
        if valor_canal is None:
            return None

        return (valor_canal / 2) + espessura + 2


class CalculoZMinimo:
    """Calcula o Z mínimo externo."""

    def calcular(self, espessura: float, deducao: float, canal_str: str):
        """
        Executa o cálculo do Z mínimo externo.
        """
        if espessura <= 0 or deducao <= 0 or not canal_str:
            return None

        canal_obj = session.query(Canal).filter_by(valor=canal_str).first()
        if not canal_obj or canal_obj.largura is None:
            return None

        return espessura + (deducao / 2) + (canal_obj.largura / 2) + 2


class CalculoRazaoRIE:
    """Calcula a razão entre Raio Interno e Espessura."""

    def calcular(self, espessura: float, raio_interno: float):
        """
        Executa o cálculo da razão RI/E.
        """
        if espessura <= 0 or raio_interno <= 0:
            return None

        razao = raio_interno / espessura
        return min(razao, 10.0)


class CalculoForca:
    """Calcula a força de dobra necessária."""

    @staticmethod
    def _obter_forca_db(espessura_valor, material_nome, canal_valor):
        """Busca o valor da força no banco de dados."""
        try:
            espessura_obj = (
                session.query(Espessura).filter_by(valor=espessura_valor).first()
            )
            material_obj = session.query(Material).filter_by(nome=material_nome).first()
            canal_obj = session.query(Canal).filter_by(valor=canal_valor).first()

            if not all([espessura_obj, material_obj, canal_obj]):
                return None, None

            deducao_obj = (
                session.query(Deducao)
                .filter(
                    Deducao.espessura_id == espessura_obj.id,
                    Deducao.material_id == material_obj.id,
                    Deducao.canal_id == canal_obj.id,
                )
                .first()
            )

            return deducao_obj.forca if deducao_obj else None, canal_obj
        except (AttributeError, TypeError, ValueError):
            return None, None

    def calcular(self, comprimento: float, espessura: float, material: str, canal: str):
        """
        Executa o cálculo da força em toneladas/m.
        """
        if not all([espessura, material, canal]):
            return None

        forca_base, canal_obj = self._obter_forca_db(espessura, material, canal)

        if forca_base is None:
            return {"forca": None, "canal_obj": canal_obj}

        toneladas_m = (
            (forca_base * comprimento) / 1000 if comprimento > 0 else forca_base
        )
        return {"forca": toneladas_m, "canal_obj": canal_obj}


class CalculoDobra:
    """Calcula as medidas de dobra, metade e blank."""

    @staticmethod
    def _calcular_medida_individual(
        valor_dobra, deducao, pos_atual, blocos_preenchidos
    ):
        """
        Calcula a medida de uma única dobra, considerando sua posição no bloco.
        """
        bloco_encontrado = None
        for bloco in blocos_preenchidos:
            if pos_atual in bloco:
                bloco_encontrado = bloco
                break

        if bloco_encontrado is None:
            return 0.0

        pos_no_bloco = bloco_encontrado.index(pos_atual)

        # PYLINT R1714: Corrigido para usar 'in'
        if len(bloco_encontrado) == 1 or pos_no_bloco in (0, len(bloco_encontrado) - 1):
            return valor_dobra - deducao / 2

        return valor_dobra - deducao

    def calcular_coluna(self, valores_dobras: List[float], deducao: float):
        """
        Calcula todas as dobras e o blank para uma coluna específica.
        """
        if deducao <= 0:
            return None

        preenchidos = [v > 0 for v in valores_dobras]
        blocos = []
        bloco_atual = []
        for i, preenchido in enumerate(preenchidos):
            if preenchido:
                bloco_atual.append(i)
            elif bloco_atual:
                blocos.append(bloco_atual)
                bloco_atual = []
        if bloco_atual:
            blocos.append(bloco_atual)

        resultados = []
        blank_total = 0
        for i, dobra_valor in enumerate(valores_dobras):
            if dobra_valor <= 0:
                resultados.append({"medida": None, "metade": None})
                continue

            medida = self._calcular_medida_individual(dobra_valor, deducao, i, blocos)
            metade = medida / 2
            blank_total += medida
            resultados.append({"medida": medida, "metade": metade})

        return {"resultados": resultados, "blank_total": blank_total}
