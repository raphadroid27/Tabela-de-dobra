"""
Módulo de Cálculos para o Aplicativo de Dobras.

Este módulo contém todas as funções e classes responsáveis por realizar
os cálculos matemáticos e lógicos do sistema. As funções aqui presentes
capturam os dados brutos dos widgets (passados como argumentos),
processam-nos e retornam os resultados, sem modificar diretamente a interface.
"""

from math import pi
import re
from src.config import globals as g
from src.models.models import Canal, Espessura, Material, Deducao
from src.utils.banco_dados import session


# --- FUNÇÕES DE CAPTURA E CONVERSÃO DE DADOS DE WIDGETS ---

def obter_valor_widget(widget, metodo='get', default_value=''):
    """
    Verifica se um widget está inicializado e obtém seu valor.

    Args:
        widget: O widget a ser verificado.
        metodo (str): O método a ser chamado ('get', 'text', 'currentText').
        default_value: Valor padrão a ser retornado se o widget for inválido.

    Returns:
        O valor do widget ou o valor padrão.
    """
    if widget is None:
        return default_value

    try:
        if metodo in ('get', 'text') and hasattr(widget, 'text'):
            return widget.text()
        if metodo == 'currentText' and hasattr(widget, 'currentText'):
            return widget.currentText() or default_value
    except (AttributeError, TypeError):
        return default_value
    return default_value


def converter_para_float(valor_str, default_value=0.0):
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
        return float(valor_str.replace(' Copiado!', '').replace(',', '.'))
    except (ValueError, TypeError):
        return default_value


# --- CLASSES DE CÁLCULO ---

class CalculoDeducaoDB:
    """Busca a dedução e observação do banco de dados."""

    def buscar(self):
        """
        Busca a dedução no banco de dados com base nos widgets selecionados.

        Returns:
            dict: {'valor': float/str, 'obs': str} ou None
        """
        material_nome = obter_valor_widget(g.MAT_COMB, 'currentText')
        espessura_str = obter_valor_widget(g.ESP_COMB, 'currentText')
        canal_valor = obter_valor_widget(g.CANAL_COMB, 'currentText')

        if not all([material_nome, espessura_str, canal_valor]):
            return None

        try:
            espessura_valor = float(espessura_str)
            espessura_obj = session.query(Espessura).filter_by(
                valor=espessura_valor).first()
            material_obj = session.query(Material).filter_by(
                nome=material_nome).first()
            canal_obj = session.query(Canal).filter_by(
                valor=canal_valor).first()

            if not all([espessura_obj, material_obj, canal_obj]):
                return {'valor': 'N/A', 'obs': 'Combinação não encontrada.'}

            deducao_obj = session.query(Deducao).filter(
                Deducao.espessura_id == espessura_obj.id,
                Deducao.material_id == material_obj.id,
                Deducao.canal_id == canal_obj.id
            ).first()

            if deducao_obj:
                return {'valor': deducao_obj.valor, 'obs': deducao_obj.observacao or ''}

            return {'valor': 'N/A', 'obs': 'Dedução não encontrada para esta combinação.'}

        except ValueError:
            return None


class CalculoDeducao:
    """Calcula a dedução a ser utilizada, lendo da UI."""

    @staticmethod
    def obter_deducao_usada():
        """
        Obtém o valor da dedução, priorizando a dedução específica.

        Returns:
            tuple: (valor_deducao, usa_deducao_especifica)
        """
        deducao_espec_str = obter_valor_widget(g.DED_ESPEC_ENTRY, 'text')
        deducao_espec = converter_para_float(deducao_espec_str)

        if deducao_espec > 0:
            return deducao_espec, True

        deducao_label_str = obter_valor_widget(g.DED_LBL, 'text')
        deducao_label = converter_para_float(deducao_label_str)
        return deducao_label, False


class CalculoFatorK:
    """Calcula o Fator K e o Offset."""

    @staticmethod
    def _formula_fator_k(espessura, deducao, raio_interno):
        """Fórmula para calcular o Fator K."""
        if espessura == 0:
            return 0.0
        numerador = 4 * (espessura - (deducao / 2) +
                         raio_interno) - (pi * raio_interno)
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
            r1, r2 = razoes[i], razoes[i+1]
            if r1 <= razao_re <= r2:
                k1, k2 = g.RAIO_K[r1], g.RAIO_K[r2]
                return k1 + (k2 - k1) * (razao_re - r1) / (r2 - r1)
        return g.RAIO_K[razoes[-1]]

    def calcular(self):
        """
        Executa o cálculo do Fator K e Offset.

        Returns:
            dict: {'fator_k': float, 'offset': float, 'especifico': bool} ou None
        """
        espessura = converter_para_float(
            obter_valor_widget(g.ESP_COMB, 'currentText'))
        raio_interno = converter_para_float(
            obter_valor_widget(g.RI_ENTRY, 'text'))

        if raio_interno <= 0 or espessura <= 0:
            return None

        deducao_usada, usa_especifica = CalculoDeducao.obter_deducao_usada()

        if deducao_usada > 0:
            fator_k = self._formula_fator_k(
                espessura, deducao_usada, raio_interno)
        else:
            razao_re = raio_interno / espessura if espessura > 0 else 0
            fator_k = self._obter_fator_k_tabela(razao_re)

        offset = fator_k * espessura
        return {'fator_k': fator_k, 'offset': offset, 'especifico': usa_especifica}


class CalculoAbaMinima:
    """Calcula a aba mínima externa."""

    @staticmethod
    def _extrair_valor_canal(canal_str):
        """Extrai o valor numérico de uma string de canal."""
        numeros = re.findall(r'\d+\.?\d*', canal_str)
        return float(numeros[0]) if numeros else None

    def calcular(self):
        """
        Executa o cálculo da aba mínima externa.

        Returns:
            float: O valor da aba mínima, ou None em caso de erro.
        """
        canal_str = obter_valor_widget(g.CANAL_COMB, 'currentText')
        espessura = converter_para_float(
            obter_valor_widget(g.ESP_COMB, 'currentText'))

        if not canal_str or espessura <= 0:
            return None

        valor_canal = self._extrair_valor_canal(canal_str)
        if valor_canal is None:
            return None

        return (valor_canal / 2) + espessura + 2


class CalculoZMinimo:
    """Calcula o Z mínimo externo."""

    def calcular(self):
        """
        Executa o cálculo do Z mínimo externo.

        Returns:
            float: O valor do Z mínimo, ou None se os dados forem insuficientes.
        """
        espessura = converter_para_float(
            obter_valor_widget(g.ESP_COMB, 'currentText'))
        deducao, _ = CalculoDeducao.obter_deducao_usada()
        canal_str = obter_valor_widget(g.CANAL_COMB, 'currentText')

        if espessura <= 0 or deducao <= 0 or not canal_str:
            return None

        canal_obj = session.query(Canal).filter_by(valor=canal_str).first()
        if not canal_obj or canal_obj.largura is None:
            return None

        return espessura + (deducao / 2) + (canal_obj.largura / 2) + 2


class CalculoRazaoRIE:
    """Calcula a razão entre Raio Interno e Espessura."""

    def calcular(self):
        """
        Executa o cálculo da razão RI/E.

        Returns:
            float: O valor da razão, ou None se os dados forem insuficientes.
        """
        espessura = converter_para_float(
            obter_valor_widget(g.ESP_COMB, 'currentText'))
        raio_interno = converter_para_float(
            obter_valor_widget(g.RI_ENTRY, 'text'))

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
            espessura_obj = session.query(Espessura).filter_by(
                valor=espessura_valor).first()
            material_obj = session.query(Material).filter_by(
                nome=material_nome).first()
            canal_obj = session.query(Canal).filter_by(
                valor=canal_valor).first()

            if not all([espessura_obj, material_obj, canal_obj]):
                return None, None

            deducao_obj = session.query(Deducao).filter(
                Deducao.espessura_id == espessura_obj.id,
                Deducao.material_id == material_obj.id,
                Deducao.canal_id == canal_obj.id
            ).first()

            return deducao_obj.forca if deducao_obj else None, canal_obj
        except (AttributeError, TypeError, ValueError):
            return None, None

    def calcular(self):
        """
        Executa o cálculo da força em toneladas/m.

        Returns:
            dict: {'forca': float, 'canal_obj': Canal, 'comprimento': float} ou None
        """
        comprimento = converter_para_float(
            obter_valor_widget(g.COMPR_ENTRY, 'text'))
        espessura = converter_para_float(
            obter_valor_widget(g.ESP_COMB, 'currentText'))
        material = obter_valor_widget(g.MAT_COMB, 'currentText')
        canal = obter_valor_widget(g.CANAL_COMB, 'currentText')

        if not all([espessura, material, canal]):
            return None

        forca_base, canal_obj = self._obter_forca_db(
            espessura, material, canal)

        if forca_base is None:
            return {'forca': None, 'canal_obj': canal_obj, 'comprimento': comprimento}

        toneladas_m = (forca_base * comprimento) / \
            1000 if comprimento > 0 else forca_base
        return {'forca': toneladas_m, 'canal_obj': canal_obj, 'comprimento': comprimento}


class CalculoDobra:
    """Calcula as medidas de dobra, metade e blank."""

    @staticmethod
    def _calcular_medida_individual(dobra, deducao, pos_atual, blocos_preenchidos):
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
        valor_dobra = converter_para_float(dobra)

        # PYLINT R1714: Corrigido para usar 'in'
        if len(bloco_encontrado) == 1 or pos_no_bloco in (0, len(bloco_encontrado) - 1):
            return valor_dobra - deducao / 2

        return valor_dobra - deducao

    def calcular_coluna(self, w):
        """
        Calcula todas as dobras e o blank para uma coluna específica.

        Args:
            w (str): O identificador da coluna ('a' ou 'b').

        Returns:
            dict: {'resultados': list, 'blank_total': float} ou None
        """
        deducao, _ = CalculoDeducao.obter_deducao_usada()
        if deducao <= 0:
            return None

        valores_dobras_str = [
            obter_valor_widget(getattr(g, f'aba{i}_entry_{w}', None), 'text')
            for i in range(1, g.N)
        ]

        preenchidos = [bool(v.strip()) for v in valores_dobras_str]
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
        for i, dobra_str in enumerate(valores_dobras_str):
            if not dobra_str.strip():
                resultados.append({'medida': None, 'metade': None})
                continue

            medida = self._calcular_medida_individual(
                dobra_str, deducao, i, blocos)
            metade = medida / 2
            blank_total += medida
            resultados.append({'medida': medida, 'metade': metade})

        return {'resultados': resultados, 'blank_total': blank_total}
